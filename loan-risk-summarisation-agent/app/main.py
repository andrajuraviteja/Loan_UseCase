from pathlib import Path
import os
import re
import sqlite3
from datetime import datetime

import fitz
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.services.risk_engine import analyse_risk
from app.services.summarizer import generate_summary

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = BASE_DIR / "data" / "loan_risk.db"

app = FastAPI(
    title="Loan Application Summarisation & Risk Flag Agent",
    version="1.0.0",
    description="FastAPI application for document ingestion, structured extraction, plain-language summarisation and risk flagging."
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                applicant_name TEXT,
                risk_level TEXT,
                risk_score INTEGER,
                summary TEXT,
                risk_flags TEXT,
                created_at TEXT NOT NULL
            )
        """)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def home():
    return FileResponse(BASE_DIR / "app" / "static" / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "service": "loan-risk-summarisation-agent"}


def extract_text_from_pdf(file_path: Path) -> str:
    try:
        document = fitz.open(file_path)
        text = "\n".join(page.get_text() for page in document)
        document.close()
        return text.strip()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read PDF: {exc}")


@app.post("/api/evaluate")
async def evaluate_loan(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF loan application.")

    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_path = UPLOAD_DIR / f"{timestamp}_{safe_name}"

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File is larger than 20 MB.")

    saved_path.write_bytes(content)
    text = extract_text_from_pdf(saved_path)

    if not text:
        raise HTTPException(status_code=400, detail="No readable text was found in the PDF.")

    analysis = analyse_risk(text)
    summary = generate_summary(analysis, text)

    flags_text = "; ".join(analysis["risk_flags"]) if analysis["risk_flags"] else "No major risk flags detected"

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(
            """
            INSERT INTO evaluations
            (filename, applicant_name, risk_level, risk_score, summary, risk_flags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                file.filename,
                analysis["fields"].get("applicant_name", "Unknown"),
                analysis["risk_level"],
                analysis["risk_score"],
                summary,
                flags_text,
                datetime.now().isoformat(timespec="seconds")
            )
        )
        evaluation_id = cur.lastrowid

    return {
        "evaluation_id": evaluation_id,
        "filename": file.filename,
        "extracted_fields": analysis["fields"],
        "risk_level": analysis["risk_level"],
        "risk_score": analysis["risk_score"],
        "risk_flags": analysis["risk_flags"],
        "summary": summary,
        "raw_text_preview": text[:1000]
    }


@app.get("/api/evaluations")
def list_evaluations():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM evaluations ORDER BY id DESC LIMIT 50"
        ).fetchall()

    return [dict(row) for row in rows]

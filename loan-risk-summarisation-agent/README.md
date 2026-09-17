# Loan Application Summarisation & Risk Flag Agent

## Business use case

A microfinance institution receives many loan applications. Relationship officers spend significant time reading documents and filling assessment forms.

This demo converts a loan application PDF into a structured officer brief.

## What the application does

1. Accepts a loan application PDF.
2. Extracts document text using PyMuPDF.
3. Extracts key fields:
   - Applicant name
   - Age
   - Monthly income
   - Employment type
   - Loan amount
   - Loan purpose
   - Co-applicant
   - Existing EMI
   - Declared income
4. Checks risk signals:
   - Missing fields
   - Income inconsistency
   - High EMI-to-income ratio
   - Unusual loan purpose
   - Loan amount high relative to income
5. Produces Low / Medium / High risk classification.
6. Generates an officer-friendly summary.
7. Stores evaluation history in a local SQLite database.
8. Provides a browser interface directly from FastAPI.

## Technologies

- Python
- FastAPI
- Uvicorn
- PyMuPDF
- SQLite
- Optional Groq API for LLM summarisation
- HTML/CSS/JavaScript frontend served by FastAPI

## Project structure

```text
loan-risk-summarisation-agent/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── risk_engine.py
│   │   └── summarizer.py
│   └── static/
│       ├── index.html
│       ├── style.css
│       └── app.js
│
├── data/
│   └── synthetic_pdfs/
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Windows setup

Open PowerShell in this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then activate again.

## Optional Groq setup

Copy `.env.example` to `.env` and put your API key in:

```text
GROQ_API_KEY=your_key_here
```

Do NOT commit `.env` to Git.

## Run the FastAPI application

```powershell
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

## Test

Use one of the PDFs in:

```text
data/synthetic_pdfs/
```

Upload it from the web page.

## Important project interpretation

The Kaggle datasets are useful as supporting structured data and reference data. The synthetic PDFs are the main document-ingestion demo because the business problem is document-heavy.

The application is a demonstration/prototype. Automated risk flags should support an officer's review, not make a final lending decision.

import os
import requests


def _fallback_summary(analysis):
    f = analysis["fields"]
    name = f.get("applicant_name") or "The applicant"
    income = f.get("monthly_income")
    amount = f.get("loan_amount")
    purpose = f.get("loan_purpose") or "not specified"
    employment = f.get("employment_type") or "not specified"
    co_applicant = f.get("co_applicant") or "not specified"

    income_text = f"₹{income:,}/month" if isinstance(income, int) else "not available"
    amount_text = f"₹{amount:,}" if isinstance(amount, int) else "not available"

    risk = analysis["risk_level"]
    flags = analysis["risk_flags"]
    flag_text = (
        " Key review points: " + "; ".join(flags) + "."
        if flags else
        " No major automated risk flags were identified from the available fields."
    )

    return (
        f"{name} has requested a loan of {amount_text} for {purpose}. "
        f"The reported monthly income is {income_text}, with employment listed as "
        f"{employment}. Co-applicant information: {co_applicant}. "
        f"Automated risk level: {risk}.{flag_text}"
    )


def generate_summary(analysis, raw_text):
    api_key = os.getenv("GROQ_API_KEY", "").strip()

    # The project works without an API key. If a Groq key is supplied,
    # use the LLM to produce a more natural officer-facing summary.
    if not api_key:
        return _fallback_summary(analysis)

    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    prompt = f"""
You are assisting a microfinance relationship officer.
Create a concise, factual loan application summary using ONLY the extracted information below.
Do not invent facts. Mention uncertainty when information is missing.
End with the automated risk level and risk flags.

Extracted analysis:
{analysis}

Source document text:
{raw_text[:7000]}
"""

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 350
            },
            timeout=45
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        # Never make the demo unusable just because the optional LLM is unavailable.
        return _fallback_summary(analysis)

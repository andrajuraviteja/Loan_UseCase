import re


FIELD_PATTERNS = {
    "applicant_name": [
        r"Applicant Name\s*:\s*(.+)",
        r"Name\s*:\s*(.+)"
    ],
    "age": [r"Age\s*:\s*(\d+)"],
    "monthly_income": [
        r"Monthly Income\s*:\s*₹?\s*([\d,]+)",
        r"Monthly Income\s*:\s*Rs\.?\s*([\d,]+)"
    ],
    "employment_type": [r"Employment Type\s*:\s*(.+)"],
    "loan_amount": [
        r"Loan Amount\s*:\s*₹?\s*([\d,]+)",
        r"Loan Amount\s*:\s*Rs\.?\s*([\d,]+)"
    ],
    "loan_purpose": [r"Loan Purpose\s*:\s*(.+)"],
    "co_applicant": [r"Co-Applicant\s*:\s*(.+)"],
    "existing_emi": [
        r"Existing EMI\s*:\s*₹?\s*([\d,]+)",
        r"Existing EMI\s*:\s*Rs\.?\s*([\d,]+)"
    ],
    "declared_income": [
        r"Declared Income\s*:\s*₹?\s*([\d,]+)",
        r"Declared Income\s*:\s*Rs\.?\s*([\d,]+)"
    ],
}


def _first_match(patterns, text):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _number(value):
    if value is None:
        return None
    return int(re.sub(r"[^\d]", "", value))


def analyse_risk(text: str):
    fields = {}
    for key, patterns in FIELD_PATTERNS.items():
        value = _first_match(patterns, text)
        if value is not None and key in {
            "age", "monthly_income", "loan_amount", "existing_emi", "declared_income"
        }:
            value = _number(value)
        fields[key] = value

    flags = []
    score = 0

    required = ["applicant_name", "monthly_income", "loan_amount", "loan_purpose"]
    missing = [f for f in required if not fields.get(f)]
    if missing:
        flags.append("Missing required field(s): " + ", ".join(missing))
        score += min(30, len(missing) * 10)

    income = fields.get("monthly_income")
    declared = fields.get("declared_income")
    if income and declared:
        difference = abs(income - declared) / max(income, 1)
        if difference >= 0.20:
            flags.append("Income inconsistency between declared and monthly income")
            score += 30

    emi = fields.get("existing_emi")
    if income and emi and emi / income > 0.50:
        flags.append("Existing EMI is high compared with monthly income")
        score += 25

    purpose = (fields.get("loan_purpose") or "").lower()
    unusual_terms = [
        "gambling", "betting", "crypto", "cryptocurrency",
        "speculation", "unknown", "cash withdrawal"
    ]
    if any(term in purpose for term in unusual_terms):
        flags.append("Loan purpose requires additional review")
        score += 25

    if fields.get("loan_amount") and income:
        if fields["loan_amount"] > income * 20:
            flags.append("Requested loan amount is high relative to monthly income")
            score += 15

    score = min(score, 100)

    if score >= 60:
        level = "High"
    elif score >= 30:
        level = "Medium"
    else:
        level = "Low"

    return {
        "fields": fields,
        "risk_score": score,
        "risk_level": level,
        "risk_flags": flags
    }

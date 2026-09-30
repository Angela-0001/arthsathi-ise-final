"""
Document Risk Analysis Pipeline — improved with better patterns and plain language.

Steps:
  1. OCR / text extraction (image, PDF, Word)
  2. Translate to English
  3. Rule-based risk detection (extended patterns)
  4. Self-verification pass
  5. Generate plain-language summary
  6. Translate back to user language
"""
import re
from typing import List
from app.services import ocr, translation
from app.schemas.document import DocumentAnalysisOut, RiskClause


RISK_PATTERNS = [
    # HIGH RISK
    (r"penalt\w*\s+(?:of\s+)?(?:rs\.?\s*)?[\d,]+", "high",
     "Penalty clause: You may be fined a specific amount."),
    (r"penalt\w+", "high",
     "Penalty clause found. Check what you will be fined for."),
    (r"forfeit\w*", "high",
     "Forfeiture clause: You could lose your money or property."),
    (r"irrevoc\w+", "high",
     "Cannot cancel: Once you sign, this cannot be undone."),
    (r"irrevec\w+", "high",
     "Cannot cancel: Once you sign, this cannot be undone."),
    (r"unlimited\s+liabilit\w*", "high",
     "Unlimited liability: You are personally responsible for all debts."),
    (r"waive[sd]?\s+(?:all\s+)?rights?", "high",
     "Rights waiver: You are giving up your legal rights."),
    (r"no\s+(?:legal\s+)?recourse", "high",
     "No recourse: You cannot take legal action if something goes wrong."),
    (r"personal\s+liabilit\w*", "high",
     "Personal liability: Your personal assets are at risk."),
    (r"cross.?default", "high",
     "Cross-default: Defaulting on one loan can trigger default on others."),
    (r"confession\s+of\s+judgment", "high",
     "Confession of judgment: Lender can take legal action without notifying you."),
    # MEDIUM RISK
    (r"interest\s+rate\s+of\s+(\d+(?:\.\d+)?)\s*%", "medium",
     "Interest rate clause found. Check if the rate is reasonable."),
    (r"\b(\d{2,3})\s*%\s*per\s+(?:annum|year|month|p\.a)", "medium",
     "High interest rate detected. Compare with bank rates before signing."),
    (r"compound(?:ed)?\s+interest", "medium",
     "Compound interest: Interest charged on interest — debt grows faster."),
    (r"no\s+refund", "medium",
     "No refund policy: You will not get your money back under any circumstances."),
    (r"arbitration\s+only", "medium",
     "Arbitration only: Disputes go to arbitration, not a court."),
    (r"personal\s+guarantee", "medium",
     "Personal guarantee: You are personally guaranteeing this loan."),
    (r"collateral", "medium",
     "Collateral clause: Your property may be seized if you default."),
    (r"balloon\s+payment", "medium",
     "Balloon payment: A large lump sum is due at the end of the loan."),
    (r"prepayment\s+penalt\w*", "medium",
     "Prepayment penalty: You will be charged for paying off the loan early."),
    (r"variable\s+(?:interest\s+)?rate", "medium",
     "Variable rate: Your interest rate can increase over time."),
    (r"acceleration\s+clause", "medium",
     "Acceleration clause: Lender can demand full payment immediately."),
    # LOW RISK
    (r"automatic\s+renewal", "low",
     "Auto-renewal: Contract extends automatically — cancel before expiry."),
    (r"subject\s+to\s+change\s+without\s+notice", "low",
     "Terms can change without informing you."),
    (r"late\s+(?:payment\s+)?fee", "low",
     "Late payment fee: Extra charge if you pay after the due date."),
    (r"non.?refundable\s+(?:deposit|fee)", "low",
     "Non-refundable deposit or fee."),
]


async def analyze_document(image_bytes: bytes, response_lang: str) -> DocumentAnalysisOut:
    # Step 1: Extract text
    raw_text = ocr.extract_text(image_bytes)

    if not raw_text or len(raw_text.strip()) < 15:
        return DocumentAnalysisOut(
            summary="Could not extract readable text from the document. Please try a clearer photo or a typed document.",
            risk_flags=[],
            verified=False,
            language=response_lang,
        )

    # Step 2: Translate to English
    text_en = await translation.to_english(raw_text, source_lang=response_lang)

    # Step 3: Detect risks
    risk_flags = _detect_risks(text_en)

    # Step 4: Self-verify
    verified, _ = _self_verify(text_en, risk_flags)

    # Step 5: Build summary
    high   = [f for f in risk_flags if f.risk_level == "high"]
    medium = [f for f in risk_flags if f.risk_level == "medium"]
    low    = [f for f in risk_flags if f.risk_level == "low"]

    summary_en = _build_summary(len(high), len(medium), len(low), raw_text)

    # Step 6: Translate back
    summary = await translation.from_english(summary_en, target_lang=response_lang)
    for flag in risk_flags:
        flag.explanation = await translation.from_english(flag.explanation, target_lang=response_lang)
        flag.clause_text = await translation.from_english(flag.clause_text, target_lang=response_lang)

    return DocumentAnalysisOut(
        summary=summary,
        risk_flags=risk_flags,
        verified=verified,
        language=response_lang,
    )


def _detect_risks(text: str) -> List[RiskClause]:
    flags = []
    text_lower = text.lower()
    seen_clauses = set()

    for pattern, level, explanation in RISK_PATTERNS:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            clause = match if isinstance(match, str) else " ".join(match)
            clause = clause.strip()[:100]
            # Deduplicate
            if clause and clause not in seen_clauses:
                seen_clauses.add(clause)
                flags.append(RiskClause(
                    clause_text=clause,
                    risk_level=level,
                    explanation=explanation,
                ))

    return flags


def _self_verify(source_text: str, flags: List[RiskClause]) -> tuple:
    source_lower = source_text.lower()
    unverified = []
    for flag in flags:
        clause_clean = re.sub(r"\s+", " ", flag.clause_text.lower().strip())
        if clause_clean and len(clause_clean) > 3 and clause_clean not in source_lower:
            unverified.append(flag)
    return len(unverified) == 0, unverified


def _build_summary(high: int, medium: int, low: int, raw_text: str) -> str:
    total = high + medium + low

    # Detect document type
    text_lower = raw_text.lower()
    doc_type = "document"
    if any(w in text_lower for w in ["loan", "borrower", "lender", "emi"]):
        doc_type = "loan agreement"
    elif any(w in text_lower for w in ["lease", "rent", "tenant", "landlord"]):
        doc_type = "rental/lease agreement"
    elif any(w in text_lower for w in ["insurance", "premium", "policyholder"]):
        doc_type = "insurance document"
    elif any(w in text_lower for w in ["sale", "deed", "property", "seller", "buyer"]):
        doc_type = "sale/property document"

    if total == 0:
        return (
            f"This appears to be a {doc_type}. "
            "No obviously risky clauses were detected. "
            "However, always read the complete document carefully before signing. "
            "Consider having it reviewed by someone you trust."
        )

    parts = []
    if high:
        parts.append(f"{high} HIGH risk clause(s) that could seriously harm you")
    if medium:
        parts.append(f"{medium} MEDIUM risk clause(s) that need careful attention")
    if low:
        parts.append(f"{low} LOW risk clause(s) to be aware of")

    advice = "DO NOT sign until you fully understand every flagged clause." if high else \
             "Review the flagged clauses carefully before signing."

    return (
        f"This appears to be a {doc_type}. "
        f"Found {total} potential risk clause(s): {'; '.join(parts)}. "
        f"{advice}"
    )

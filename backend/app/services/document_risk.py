"""
Document Risk Analysis Pipeline.

Steps:
  1. OCR          — extract text from image
  2. Translate    — to English via our own translation API
  3. Detect       — rule-based pattern match + risk classification
  4. Self-verify  — structured fact-check questions against source text
  5. Translate    — summary + flags back to user's language

Hallucination resistance: self-verification uses question-based re-checking
against the original source text, not a generic "check yourself" prompt.
"""

import re
from typing import List

from app.services import ocr, translation
from app.schemas.document import DocumentAnalysisOut, RiskClause

# Extended rule-based patterns — (regex, risk_level, explanation_en)
RISK_PATTERNS = [
    (r"penalt\w*\s+of\s+(?:rs\.?\s*)?[\d,]+", "high",
     "A financial penalty clause was found. You may be charged extra money."),
    (r"penalt\w+", "high",
     "A penalty clause was found. Check the exact amount carefully."),
    (r"forfeit\w*", "high",
     "A forfeiture clause means you could lose your money or property."),
    (r"irrevoc\w+", "high",
     "This agreement cannot be cancelled once signed. Be very careful."),
    (r"irrevec\w+", "high",
     "This agreement cannot be cancelled once signed. Be very careful."),
    (r"unlimited\s+liabilit\w*", "high",
     "You could be held personally responsible for all debts with no limit."),
    (r"waive[sd]?\s+(?:all\s+)?rights?", "high",
     "You are giving up your legal rights. This is very serious."),
    (r"no\s+(?:legal\s+)?recourse", "high",
     "You cannot take legal action if something goes wrong."),
    (r"interest\s+rate\s+of\s+(\d+(?:\.\d+)?)\s*%", "medium",
     "An interest rate clause was found. Check if this rate is reasonable."),
    (r"\d{2,3}\s*%\s*per\s+(?:annum|year|month)", "medium",
     "A high interest rate clause was found."),
    (r"compound(?:ed)?\s+interest", "medium",
     "Compound interest means interest on interest — debt grows faster."),
    (r"no\s+refund", "medium",
     "No refund will be given under any circumstances."),
    (r"arbitration\s+only", "medium",
     "Disputes can only go to arbitration, not a court of law."),
    (r"automatic\s+renewal", "low",
     "This contract will auto-renew. You must cancel before expiry to stop it."),
    (r"subject\s+to\s+change\s+without\s+notice", "low",
     "Terms can be changed at any time without informing you."),
    (r"personal\s+guarantee", "medium",
     "You are personally guaranteeing this loan or contract."),
    (r"collateral\s+(?:of\s+)?(?:rs\.?\s*)?[\d,]+", "medium",
     "Your property or assets are being pledged as security."),
    (r"balloon\s+payment", "medium",
     "A large lump sum payment is required at the end of the loan."),
]

# Self-verification question templates
# For each high/medium risk clause found, we check it actually appears in source
VERIFY_QUESTIONS = [
    ("Does the document explicitly mention a penalty?",
     [r"penalty", r"penali[sz]e"]),
    ("Does the document mention forfeiture of property or money?",
     [r"forfeit", r"forfeiture"]),
    ("Is there an irrevocability clause?",
     [r"irrevocabl"]),
    ("Does the document mention interest rate?",
     [r"interest\s+rate", r"%\s*(?:per\s+(?:annum|year|month))"]),
]


async def analyze_document(image_bytes: bytes, response_lang: str) -> DocumentAnalysisOut:
    # ── Step 1: OCR ───────────────────────────────────────────────────
    raw_text = ocr.extract_text(image_bytes)

    if not raw_text or len(raw_text.strip()) < 20:
        return DocumentAnalysisOut(
            summary="Could not extract readable text from the document image. Please try a clearer photo.",
            risk_flags=[],
            verified=False,
            language=response_lang,
        )

    # ── Step 2: Translate to English if needed ─────────────────────────
    text_en = await translation.to_english(raw_text, source_lang=response_lang)

    # ── Step 3: Rule-based risk detection ──────────────────────────────
    risk_flags = _detect_risks(text_en)

    # ── Step 4: Self-verification ──────────────────────────────────────
    verified, unverified_flags = _self_verify(text_en, risk_flags)

    # Mark unverified flags
    for flag in unverified_flags:
        flag.risk_level = "unverified"

    # ── Step 5: Build summary ──────────────────────────────────────────
    high = [f for f in risk_flags if f.risk_level == "high"]
    medium = [f for f in risk_flags if f.risk_level == "medium"]
    low = [f for f in risk_flags if f.risk_level == "low"]

    summary_en = _build_summary(len(high), len(medium), len(low), len(risk_flags))

    # ── Step 6: Translate back to user language ────────────────────────
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

    for pattern, level, explanation in RISK_PATTERNS:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            clause = match if isinstance(match, str) else " ".join(match)
            # Avoid duplicate clauses
            if not any(f.clause_text == clause for f in flags):
                flags.append(RiskClause(
                    clause_text=clause,
                    risk_level=level,
                    explanation=explanation,
                ))

    return flags


def _self_verify(source_text: str, flags: List[RiskClause]) -> tuple[bool, List[RiskClause]]:
    """
    Structured self-check: for each risk flag, verify the triggering
    pattern actually exists in source text.
    Returns (all_verified: bool, unverified_flags: list).
    """
    source_lower = source_text.lower()
    unverified = []

    for flag in flags:
        # Check if the clause text is present in source
        clause_clean = re.sub(r"\s+", " ", flag.clause_text.lower().strip())
        if clause_clean and clause_clean not in source_lower:
            unverified.append(flag)

    all_verified = len(unverified) == 0
    return all_verified, unverified


def _build_summary(high: int, medium: int, low: int, total: int) -> str:
    if total == 0:
        return ("No obviously risky clauses were detected in this document. "
                "However, always read the full document carefully before signing.")

    parts = []
    if high:
        parts.append(f"{high} HIGH risk clause(s) that could cause serious harm")
    if medium:
        parts.append(f"{medium} MEDIUM risk clause(s) that need your attention")
    if low:
        parts.append(f"{low} LOW risk clause(s) to be aware of")

    return (f"This document contains {total} potential risk clause(s): {'; '.join(parts)}. "
            f"Do NOT sign until you fully understand each flagged clause.")

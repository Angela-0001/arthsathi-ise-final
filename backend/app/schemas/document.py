from pydantic import BaseModel
from typing import List, Optional


class RiskClause(BaseModel):
    clause_text: str
    risk_level: str          # "high" | "medium" | "low"
    explanation: str


class DocumentAnalysisOut(BaseModel):
    summary: str
    risk_flags: List[RiskClause]
    verified: bool           # True if self-check pass found no contradictions
    language: str

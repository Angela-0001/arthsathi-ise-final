from pydantic import BaseModel
from typing import List


class RoadmapStep(BaseModel):
    priority: int
    action: str
    reason: str
    amount: float | None = None


class RoadmapOut(BaseModel):
    monthly_income: float
    total_debt: float
    steps: List[RoadmapStep]
    summary: str

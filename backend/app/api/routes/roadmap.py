"""
Financial roadmap routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.roadmap_engine import generate
from app.schemas.roadmap import RoadmapOut

router = APIRouter()


@router.get("/", response_model=RoadmapOut)
async def get_roadmap(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns a rule-based, personalized financial roadmap for the user."""
    return await generate(current_user)

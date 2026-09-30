"""
User profile routes — update income, occupation, state, goals etc.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    preferred_language: Optional[str] = None
    monthly_income: Optional[float] = None
    occupation: Optional[str] = None
    state: Optional[str] = None
    age: Optional[int] = None
    goals: Optional[dict] = None


class ProfileOut(BaseModel):
    id: int
    phone: str
    full_name: Optional[str]
    preferred_language: str
    monthly_income: Optional[float]
    occupation: Optional[str]
    state: Optional[str]
    age: Optional[int]
    goals: Optional[dict]
    aadhaar_verified: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=ProfileOut)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/", response_model=ProfileOut)
async def update_profile(
    body: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    await db.commit()
    await db.refresh(current_user)
    return current_user

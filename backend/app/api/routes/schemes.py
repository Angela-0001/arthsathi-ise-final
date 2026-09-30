from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.interaction import ItemInteraction
from app.services.scheme_matcher import match_for_user, get_scheme_detail, update_engagement_weight
from app.schemas.scheme import SchemeOut

router = APIRouter()


@router.get("/match", response_model=List[SchemeOut])
async def match_schemes(
    lang: str = Query("hi"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await match_for_user(current_user, db, lang)


@router.get("/{scheme_id}", response_model=SchemeOut)
async def scheme_detail(
    scheme_id: str,
    lang: str = Query("hi"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_scheme_detail(scheme_id, db, lang)


@router.post("/{scheme_id}/engage")
async def record_engagement(
    scheme_id: str,
    interaction_type: str = Query("clicked", description="applied | clicked | dismissed"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Save to DB
    interaction = ItemInteraction(
        user_id=current_user.id,
        item_id=scheme_id,
        item_type="scheme",
        interaction_type=interaction_type,
    )
    db.add(interaction)
    await db.commit()

    # Update adaptive weight
    await update_engagement_weight(scheme_id, "scheme", db)
    return {"message": "recorded"}

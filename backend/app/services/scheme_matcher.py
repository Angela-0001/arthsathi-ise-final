"""
Scheme matching — uses our own SchemeRecommender from arthsathi-ml.
Falls back to DB-only rule-based matching if ML artifacts not built yet.
"""
import sys
from pathlib import Path
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.user import User
from app.models.scheme import Scheme
from app.models.interaction import AdaptiveWeight
from app.schemas.scheme import SchemeOut
from app.services import translation

# Add arthsathi-ml to path
_ML_PATH = str(Path(__file__).parent.parent.parent.parent / "arthsathi-ml")
if _ML_PATH not in sys.path:
    sys.path.insert(0, _ML_PATH)


def _get_recommender():
    """Lazy-load the ML recommender. Returns None if artifacts not built yet."""
    try:
        import os
        # Try absolute path from project root
        ml_path = str(Path(__file__).resolve().parent.parent.parent.parent / "arthsathi-ml")
        if ml_path not in sys.path:
            sys.path.insert(0, ml_path)
        from models.scheme_recommender.recommender import SchemeRecommender
        return SchemeRecommender()
    except Exception as e:
        print(f"[scheme_matcher] ML recommender not available: {e}. Using DB fallback.")
        return None
        from models.scheme_recommender.recommender import SchemeRecommender
        return SchemeRecommender()
    except Exception as e:
        print(f"[scheme_matcher] ML recommender not available: {e}. Using DB fallback.")
        return None


async def match_for_user(user: User, db: AsyncSession, lang: str) -> List[SchemeOut]:
    recommender = _get_recommender()

    if recommender:
        # Use ML recommender
        profile = _user_to_profile(user)
        results = recommender.recommend(profile, top_k=20)
        return [_ml_result_to_out(r) for r in results]
    else:
        # Fallback: DB rule-based
        return await _db_match(user, db, lang)


async def get_scheme_detail(scheme_id: str, db: AsyncSession, lang: str) -> SchemeOut:
    result = await db.execute(select(Scheme).where(Scheme.scheme_id == scheme_id))
    scheme = result.scalar_one_or_none()
    if not scheme:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Scheme not found")
    return await _db_scheme_to_out(scheme, lang)


async def update_engagement_weight(scheme_id: str, item_type: str, db: AsyncSession) -> None:
    """Update adaptive weight in DB (Thompson Sampling alpha increment)."""
    from datetime import datetime

    result = await db.execute(
        select(AdaptiveWeight).where(AdaptiveWeight.item_id == scheme_id)
    )
    weight = result.scalar_one_or_none()

    if weight:
        weight.alpha = min(weight.alpha + 0.3, 1000.0)
        weight.updated_at = datetime.utcnow()
    else:
        weight = AdaptiveWeight(
            item_id=scheme_id,
            item_type=item_type,
            alpha=1.3,
            beta=1.0,
        )
        db.add(weight)

    await db.commit()

    # Also update ML recommender bandit if available
    try:
        from models.scheme_recommender.recommender import SchemeRecommender
        rec = SchemeRecommender()
        rec.record_interaction(scheme_id, "applied")
    except Exception:
        pass


def _user_to_profile(user: User) -> dict:
    goals = user.goals or {}
    return {
        "age": user.age,
        "gender": "all",
        "occupation": user.occupation or "",
        "state": user.state or "",
        "annual_income": (user.monthly_income or 0) * 12,
        "bank_account": True,
        "aadhaar": user.aadhaar_verified,
        "goals": goals.get("interests", []),
    }


def _ml_result_to_out(r: dict) -> SchemeOut:
    return SchemeOut(
        scheme_id=r["id"],
        name=r["name"],
        description=r["description"],
        ministry=None,
        category=r.get("category"),
        benefit_value=None,
        application_url=r.get("application_url"),
        translated_name=r["name"],
        translated_description=r.get("benefits") or r["description"],
    )


async def _db_match(user: User, db: AsyncSession, lang: str) -> List[SchemeOut]:
    result = await db.execute(select(Scheme).where(Scheme.is_active == True))
    all_schemes = result.scalars().all()
    # If user has no profile data, skip eligibility filter and return all schemes ranked
    if not user.age and not user.monthly_income and not user.occupation:
        ranked = sorted(all_schemes, key=lambda s: s.engagement_weight * (s.benefit_value or 1), reverse=True)
    else:
        eligible = [s for s in all_schemes if _is_eligible(user, s)]
        ranked = sorted(eligible, key=lambda s: s.engagement_weight * (s.benefit_value or 1), reverse=True)
    return [await _db_scheme_to_out(s, lang) for s in ranked[:20]]


def _is_eligible(user: User, scheme: Scheme) -> bool:
    if scheme.min_age and user.age and user.age < scheme.min_age:
        return False
    if scheme.max_age and user.age and user.age > scheme.max_age:
        return False
    if scheme.max_income and user.monthly_income and user.monthly_income > scheme.max_income:
        return False
    if scheme.eligible_states and user.state and user.state not in scheme.eligible_states:
        return False
    return True


async def _db_scheme_to_out(scheme: Scheme, lang: str) -> SchemeOut:
    name = scheme.name
    description = scheme.description
    if lang not in ("en", "eng"):
        name = await translation.from_english(name, target_lang=lang)
        description = await translation.from_english(description, target_lang=lang)
    return SchemeOut(
        scheme_id=scheme.scheme_id,
        name=scheme.name,
        description=scheme.description,
        ministry=scheme.ministry,
        category=scheme.category,
        benefit_value=scheme.benefit_value,
        application_url=scheme.application_url,
        translated_name=name,
        translated_description=description,
    )

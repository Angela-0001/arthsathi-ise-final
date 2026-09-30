"""
Seed the database with schemes and insurance data from arthsathi-ml.
Run once on first startup, or call manually.
"""
import json
import sys
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


ML_DATA_PATH = Path(__file__).parent.parent.parent.parent / "arthsathi-ml" / "data"


async def seed_schemes(db: AsyncSession) -> None:
    from app.models.scheme import Scheme

    schemes_file = ML_DATA_PATH / "schemes" / "schemes_clean.jsonl"
    if not schemes_file.exists():
        print("[seed] No schemes file found. Run data collection in arthsathi-ml first.")
        return

    records = [json.loads(l) for l in schemes_file.read_text(encoding="utf-8").splitlines() if l.strip()]
    new_count = 0

    for r in records:
        scheme_id = r.get("id") or r.get("scheme_id", "")
        if not scheme_id:
            continue

        existing = await db.execute(select(Scheme).where(Scheme.scheme_id == scheme_id))
        if existing.scalar_one_or_none():
            continue  # already seeded

        scheme = Scheme(
            scheme_id=scheme_id,
            name=r.get("name", ""),
            description=r.get("description", "") or r.get("benefits", ""),
            ministry=r.get("ministry"),
            category=r.get("category"),
            min_age=r.get("min_age"),
            max_age=r.get("max_age"),
            max_income=r.get("max_income_annual"),
            eligible_states=r.get("eligible_states") or [],
            eligible_occupations=r.get("eligible_occupations") or [],
            benefit_value=None,
            application_url=r.get("application_url"),
            is_active=True,
        )
        db.add(scheme)
        new_count += 1

    await db.commit()
    print(f"[seed] Seeded {new_count} new schemes")


async def run_seed(db: AsyncSession) -> None:
    await seed_schemes(db)

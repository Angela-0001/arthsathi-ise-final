"""
Weekly scheme refresh — pulls from myScheme and upserts into DB.
Runs as a background job. Fails silently if myScheme is unreachable.
"""
import httpx
from datetime import datetime
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.scheme import Scheme

MYSCHEME_API = "https://api.myscheme.gov.in/search/v4/schemes"


async def refresh_schemes() -> None:
    print(f"[scheme_pipeline] Refresh started at {datetime.utcnow()}")
    try:
        schemes_data = await _fetch_schemes()
        if not schemes_data:
            print("[scheme_pipeline] No data from myScheme, skipping refresh")
            return

        async with AsyncSessionLocal() as db:
            for item in schemes_data:
                await _upsert(db, item)
            await db.commit()

        print(f"[scheme_pipeline] Refreshed {len(schemes_data)} schemes")
    except Exception as e:
        print(f"[scheme_pipeline] Refresh failed: {e}")


async def _fetch_schemes() -> list:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(MYSCHEME_API, params={"from": 0, "size": 200})
            resp.raise_for_status()
            return resp.json().get("hits", {}).get("hits", [])
    except Exception:
        return []


async def _upsert(db, item: dict) -> None:
    src = item.get("_source", {})
    scheme_id = item.get("_id", "")
    if not scheme_id:
        return

    result = await db.execute(select(Scheme).where(Scheme.scheme_id == scheme_id))
    scheme = result.scalar_one_or_none()
    if not scheme:
        scheme = Scheme(scheme_id=scheme_id)
        db.add(scheme)

    scheme.name = src.get("schemeName", "") or scheme_id
    scheme.description = src.get("schemeShortTitle", "") or scheme.name
    scheme.ministry = src.get("ministryName")
    scheme.category = src.get("schemeCategory")
    scheme.application_url = src.get("applicationUrl")
    scheme.last_refreshed = datetime.utcnow()
    scheme.is_active = True


def start_scheduler():
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(refresh_schemes, "interval", weeks=1, id="scheme_refresh",
                      replace_existing=True)
    scheduler.start()
    print("[scheme_pipeline] Scheduler started")
    return scheduler

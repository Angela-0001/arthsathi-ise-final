from fastapi import APIRouter, UploadFile, File, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.document import DocumentAnalysis
from app.services.document_risk import analyze_document
from app.schemas.document import DocumentAnalysisOut

router = APIRouter()


async def get_optional_user(request: Request, db: AsyncSession = Depends(get_db)) -> Optional[User]:
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth.split(" ", 1)[1]
        from fastapi.security import HTTPAuthorizationCredentials
        from app.core.security import get_current_user
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        return await get_current_user(credentials=creds, db=db)
    except Exception:
        return None


@router.post("/analyze", response_model=DocumentAnalysisOut)
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    lang: str = Query("hi"),
    db: AsyncSession = Depends(get_db),
):
    """
    Accepts: images (JPG/PNG), PDFs, Word (.docx).
    Returns risk flags + plain-language summary.
    Auth optional — bots can call without token.
    """
    image_bytes = await file.read()
    result = await analyze_document(image_bytes, lang)

    current_user = await get_optional_user(request, db)
    if current_user:
        high_count   = sum(1 for f in result.risk_flags if f.risk_level == "high")
        medium_count = sum(1 for f in result.risk_flags if f.risk_level == "medium")
        record = DocumentAnalysis(
            user_id=current_user.id,
            summary=result.summary,
            risk_flags=[f.model_dump() for f in result.risk_flags],
            verified=result.verified,
            language=result.language,
            high_risk_count=high_count,
            medium_risk_count=medium_count,
        )
        db.add(record)
        await db.commit()

    return result


@router.get("/summary/latest")
async def latest_summary(db: AsyncSession = Depends(get_db)):
    """Returns summary of the most recently analyzed document. No auth required for bot."""
    result = await db.execute(
        select(DocumentAnalysis)
        .order_by(DocumentAnalysis.created_at.desc())
        .limit(1)
    )
    record = result.scalar_one_or_none()
    if not record:
        return {"message": "No documents analyzed yet. Send a document photo to analyze it."}

    return {
        "summary": record.summary,
        "high_risk_count": record.high_risk_count,
        "medium_risk_count": record.medium_risk_count,
        "risk_flags": record.risk_flags or [],
        "analyzed_at": record.created_at.isoformat(),
    }


@router.get("/history")
async def history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(DocumentAnalysis)
        .where(DocumentAnalysis.user_id == current_user.id)
        .order_by(DocumentAnalysis.created_at.desc())
        .limit(20)
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "summary": r.summary,
            "high_risk_count": r.high_risk_count,
            "medium_risk_count": r.medium_risk_count,
            "verified": r.verified,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]

"""
Form automation routes — Playwright-based auto-fill for scheme applications.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.security import get_current_user
from app.models.user import User
from app.services.form_filler import prefill_form

router = APIRouter()


class FormRequest(BaseModel):
    scheme_id: str
    application_url: str


@router.post("/prefill")
async def prefill(
    body: FormRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Uses Playwright to pre-fill a scheme application form with user's verified profile data.
    Returns a preview of filled fields for user confirmation before submission.
    """
    preview = await prefill_form(body.application_url, current_user)
    return {"preview": preview, "message": "Please review and confirm before submitting."}

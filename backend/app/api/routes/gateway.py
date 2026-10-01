"""
Channel Gateway — normalizes input from Web, WhatsApp, Telegram, and IVR
into a single NormalizedMessage, then dispatches to the right service.
"""
from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import Response
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.core.database import get_db
from app.schemas.gateway import NormalizedMessage, GatewayResponse, Channel, Intent
from app.services import speech, translation

router = APIRouter()


@router.post("/message", response_model=GatewayResponse)
async def handle_message(
    msg: NormalizedMessage,
    db: AsyncSession = Depends(get_db),
):
    text = msg.raw_text

    # Transcribe audio if provided
    if msg.audio_url and not text:
        text = await speech.transcribe(msg.audio_url, msg.detected_language)

    # Translate to English for core logic
    text_en = await translation.to_english(text or "", source_lang=msg.detected_language)

    # Dispatch
    result_text = await _dispatch(msg, text_en, db)

    # Translate response back
    response_text = await translation.from_english(result_text, target_lang=msg.detected_language)

    # TTS for IVR
    audio_url = None
    if msg.channel == Channel.ivr:
        audio_url = await speech.synthesize(response_text, msg.detected_language)

    return GatewayResponse(
        user_id=msg.user_id,
        text_response=response_text,
        audio_url=audio_url,
        language=msg.detected_language,
        intent=msg.intent,
    )


@router.post("/ivr/webhook")
async def ivr_webhook(
    CallSid: str = Form(...),
    From: str = Form(...),
    SpeechResult: Optional[str] = Form(None),
    Digits: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    msg = NormalizedMessage(
        user_id=From,
        channel=Channel.ivr,
        raw_text=SpeechResult or Digits,
        detected_language="hi",
    )
    response = await handle_message(msg, db)

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say language="hi-IN">{response.text_response}</Say>
  <Gather input="speech" action="/gateway/ivr/webhook" language="hi-IN" timeout="5"/>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


async def _dispatch(msg: NormalizedMessage, text_en: str, db: AsyncSession) -> str:
    from app.services import scheme_matcher, roadmap_engine

    # Try to get user from DB
    user = await _get_user(msg.user_id, db)

    if msg.intent == Intent.scheme_match:
        if user:
            results = await scheme_matcher.match_for_user(user, db, "en")
        else:
            # No profile — show top schemes from DB
            results = await scheme_matcher._db_match_anonymous(db)
        if not results:
            return "No schemes found. Please complete your profile on the web app for personalised results."
        top = results[:5]
        lines = [f"{i+1}. {s.name}" for i, s in enumerate(top)]
        return "📋 Top Government Schemes:\n\n" + "\n".join(lines) + "\n\nVisit the web app to see your eligible schemes."

    if msg.intent == Intent.financial_roadmap:
        if user:
            roadmap = await roadmap_engine.generate(user)
            lines = [f"{s.priority}. {s.action}" for s in roadmap.steps[:4]]
            return roadmap.summary + "\n\n" + "\n".join(lines)
        return "🗺️ To get your personalised financial roadmap, please complete your profile on the web app first.\n\nVisit: http://localhost:3000/profile"

    if msg.intent == Intent.document_analysis:
        return "Please upload a photo of your document for analysis."

    # Keyword-based intent detection for WhatsApp plain text
    text_lower = (text_en or "").lower().strip()
    if text_lower in ("1", "schemes", "scheme", "योजना", "yojana"):
        msg.intent = Intent.scheme_match
        if user:
            results = await scheme_matcher.match_for_user(user, db, "en")
            if results:
                top = results[:3]
                lines = [f"{i+1}. {s.name}" for i, s in enumerate(top)]
                return "Top schemes for you:\n" + "\n".join(lines)
        return "Please complete your profile first to get scheme recommendations."

    if text_lower in ("2", "roadmap", "financial", "वित्त"):
        if user:
            roadmap = await roadmap_engine.generate(user)
            lines = [f"{s.priority}. {s.action}" for s in roadmap.steps[:4]]
            return roadmap.summary + "\n\n" + "\n".join(lines)
        return "Please complete your profile first."

    if text_lower in ("3", "document", "analyze", "दस्तावेज़"):
        return "Please send a photo or PDF of your document and I will analyze it for risky clauses."

    # Default — show menu
    if not msg.intent or msg.intent == Intent.general_query:
        return (
            "🙏 नमस्ते! ArthSathi में आपका स्वागत है।\n\n"
            "Hello! I'm ArthSathi. Type:\n\n"
            "1️⃣ *1* — Government Schemes\n"
            "2️⃣ *2* — Financial Roadmap\n"
            "3️⃣ *3* — Analyze a Document\n\n"
            "Or send a photo/PDF of any document to check for risky clauses."
        )

    return text_en or "How can I help you today?"


async def _get_user(user_id: str, db: AsyncSession):
    """Try to find user by phone or string ID."""
    try:
        from sqlalchemy import select
        from app.models.user import User

        # user_id might be phone number (WhatsApp/IVR) or DB ID (web)
        if user_id.lstrip("whatsapp:+").isdigit():
            phone = user_id.replace("whatsapp:", "").lstrip("+")
            result = await db.execute(select(User).where(User.phone.contains(phone[-10:])))
        else:
            result = await db.execute(select(User).where(User.id == int(user_id)))
        return result.scalar_one_or_none()
    except Exception:
        return None

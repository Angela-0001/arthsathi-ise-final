from pydantic import BaseModel
from typing import Literal, Optional
from enum import Enum


class Channel(str, Enum):
    web = "web"
    whatsapp = "whatsapp"
    telegram = "telegram"
    ivr = "ivr"


class Intent(str, Enum):
    document_analysis = "document_analysis"
    scheme_match = "scheme_match"
    financial_roadmap = "financial_roadmap"
    form_fill = "form_fill"
    general_query = "general_query"


class NormalizedMessage(BaseModel):
    """Common internal message format produced by the Channel Gateway."""
    user_id: str
    channel: Channel
    raw_text: Optional[str] = None
    audio_url: Optional[str] = None       # for voice-note / IVR input
    detected_language: str = "hi"         # BCP-47 / ISO 639
    intent: Optional[Intent] = None
    payload: Optional[dict] = None        # channel-specific extras


class GatewayResponse(BaseModel):
    user_id: str
    text_response: str
    audio_url: Optional[str] = None       # TTS output URL
    language: str
    intent: Optional[Intent] = None
    data: Optional[dict] = None

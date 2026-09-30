"""
Translation service — calls our OWN translation API.
Our model lives in arthsathi-ml/translation/serve.py, running on port 5001.
If not running, returns original text (graceful fallback during development).
"""
import httpx
from app.core.config import settings


async def to_english(text: str, source_lang: str) -> str:
    if not text or not text.strip():
        return text
    if source_lang in ("en", "eng"):
        return text
    return await _translate(text, src=source_lang, tgt="en")


async def from_english(text: str, target_lang: str) -> str:
    if not text or not text.strip():
        return text
    if target_lang in ("en", "eng"):
        return text
    return await _translate(text, src="en", tgt=target_lang)


async def _translate(text: str, src: str, tgt: str) -> str:
    # Only hi and mr supported by our model
    if tgt not in ("hi", "mr", "en") or src not in ("hi", "mr", "en"):
        return text

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{settings.TRANSLATION_API_URL}/translate",
                json={"text": text, "src_lang": src, "tgt_lang": tgt, "beam": True},
            )
            resp.raise_for_status()
            return resp.json()["translated_text"]
    except httpx.ConnectError:
        # Our translation server not running yet — return original text
        return text
    except Exception as e:
        print(f"[translation] Error: {e}")
        return text

"""
Speech service — offline ASR + TTS.
ASR: Vosk (local, no API)
TTS: pyttsx3 (local, no API)
Falls back gracefully if models not downloaded yet.
"""
import os
import sys
import tempfile
import asyncio
from pathlib import Path

# Path to arthsathi-ml
_ML_PATH = str(Path(__file__).resolve().parent.parent.parent.parent / "arthsathi-ml")


def _add_ml_path():
    if _ML_PATH not in sys.path:
        sys.path.insert(0, _ML_PATH)


async def transcribe(audio_url: str, language: str) -> str:
    """Download audio and transcribe using Vosk."""
    import httpx

    if audio_url.startswith("http"):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(audio_url)
                resp.raise_for_status()
                audio_bytes = resp.content
        except Exception as e:
            print(f"[speech] Could not download audio: {e}")
            return ""
    else:
        try:
            audio_bytes = Path(audio_url).read_bytes()
        except Exception:
            return ""

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_transcribe, audio_bytes, language)


def _sync_transcribe(audio_bytes: bytes, lang: str) -> str:
    _add_ml_path()
    try:
        from speech.asr import transcribe_bytes
        return transcribe_bytes(audio_bytes, lang=lang)
    except Exception as e:
        print(f"[ASR] Not available: {e}")
        return ""


async def synthesize(text: str, language: str) -> str:
    """Convert text to speech, returns path to WAV file."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_tts, text, language)


def _sync_tts(text: str, lang: str) -> str:
    _add_ml_path()
    try:
        from speech.tts import speak_text
        out_path = tempfile.mktemp(suffix=".wav")
        speak_text(text, lang=lang, output_file=out_path)
        return out_path
    except Exception as e:
        print(f"[TTS] Not available: {e}")
        return ""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Use SQLite by default so the app runs without installing PostgreSQL
    # Switch to postgresql+asyncpg://... in .env for production
    DATABASE_URL: str = "sqlite+aiosqlite:///./arthsathi.db"

    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    DIGILOCKER_CLIENT_ID: str = ""
    DIGILOCKER_CLIENT_SECRET: str = ""
    DIGILOCKER_REDIRECT_URI: str = "http://localhost:8000/auth/digilocker/callback"

    TELEGRAM_BOT_TOKEN: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # Our own ML service (arthsathi-ml/translation/serve.py)
    # Start with: cd arthsathi-ml && uvicorn translation.serve:app --port 5001
    TRANSLATION_API_URL: str = "http://localhost:5001"

    # Paths to arthsathi-ml artifacts
    SCHEME_RECOMMENDER_PATH: str = "../arthsathi-ml/models/scheme_recommender/artifacts"
    INSURANCE_RECOMMENDER_PATH: str = "../arthsathi-ml/models/insurance_recommender/artifacts"
    LM_CHECKPOINT_PATH: str = "../arthsathi-ml/language_model/checkpoints/best_lm.pt"
    VOSK_MODEL_PATH: str = "../arthsathi-ml/speech/models/vosk"

    MYSCHEME_BASE_URL: str = "https://www.myscheme.gov.in"

    class Config:
        env_file = ".env"


settings = Settings()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal

# Import all models so SQLAlchemy registers them before create_all
from app.models.user import User               # noqa: F401
from app.models.scheme import Scheme           # noqa: F401
from app.models.document import DocumentAnalysis  # noqa: F401
from app.models.interaction import ItemInteraction, AdaptiveWeight  # noqa: F401

from app.api.routes import auth, gateway, schemes, documents, roadmap, forms, profile


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all DB tables
    await init_db()

    # Seed schemes from arthsathi-ml data (silently skips if file not found)
    async with AsyncSessionLocal() as db:
        from app.services.seed import run_seed
        await run_seed(db)

    # Start weekly scheme refresh scheduler
    try:
        from app.services.scheme_pipeline import start_scheduler
        start_scheduler()
    except Exception as e:
        print(f"[startup] Scheduler not started: {e}")

    yield


app = FastAPI(
    title="ArthSathi API",
    description="AI-powered multilingual financial companion",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,      prefix="/auth",      tags=["auth"])
app.include_router(gateway.router,   prefix="/gateway",   tags=["channel-gateway"])
app.include_router(schemes.router,   prefix="/schemes",   tags=["schemes"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(roadmap.router,   prefix="/roadmap",   tags=["roadmap"])
app.include_router(forms.router,     prefix="/forms",     tags=["forms"])
app.include_router(profile.router,   prefix="/profile",   tags=["profile"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}

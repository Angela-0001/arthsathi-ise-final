"""
Stores user-scheme/insurance interactions for adaptive engine.
Replaces the JSON file approach in arthsathi-ml.
"""
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base


class ItemInteraction(Base):
    __tablename__ = "item_interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    item_id: Mapped[str] = mapped_column(String(100), index=True)   # scheme_id or insurance_id
    item_type: Mapped[str] = mapped_column(String(20))              # "scheme" | "insurance"
    interaction_type: Mapped[str] = mapped_column(String(20))       # "applied" | "clicked" | "dismissed"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AdaptiveWeight(Base):
    """
    Stores per-item Beta distribution parameters (alpha, beta) for Thompson Sampling.
    One row per item — upserted on every interaction.
    """
    __tablename__ = "adaptive_weights"

    item_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    item_type: Mapped[str] = mapped_column(String(20))
    alpha: Mapped[float] = mapped_column(Float, default=1.0)
    beta: Mapped[float] = mapped_column(Float, default=1.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

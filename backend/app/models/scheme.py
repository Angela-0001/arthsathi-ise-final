from sqlalchemy import String, Integer, Float, JSON, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base


class Scheme(Base):
    __tablename__ = "schemes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scheme_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # myScheme ID
    name: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text)
    ministry: Mapped[str | None] = mapped_column(String(200), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Eligibility criteria (hard filters)
    min_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    eligible_states: Mapped[list | None] = mapped_column(JSON, nullable=True)   # [] = all states
    eligible_occupations: Mapped[list | None] = mapped_column(JSON, nullable=True)

    benefit_value: Mapped[float | None] = mapped_column(Float, nullable=True)  # for ranking
    application_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    translations: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {lang: {name, description}}

    # Adaptive ranking weight (updated by engagement)
    engagement_weight: Mapped[float] = mapped_column(Float, default=1.0)

    last_refreshed: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(default=True)

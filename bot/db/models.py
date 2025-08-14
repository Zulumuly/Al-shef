from __future__ import annotations
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, String, Integer, Text
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
from .database import Base

class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)  # Telegram user_id
    plan_md: Mapped[str] = mapped_column(Text)  # сам план в Markdown/тексте

    requested_days: Mapped[int] = mapped_column(Integer)
    meals_per_day: Mapped[int] = mapped_column(Integer)
    feasible_days: Mapped[int | None] = mapped_column(Integer, nullable=True)  # «посильные» дни, если не хватило
    decision: Mapped[str | None] = mapped_column(String(32), nullable=True)    # ok/reduce/need_purchases/fallback

    ingredients_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # исходные продукты в JSON-строке

    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

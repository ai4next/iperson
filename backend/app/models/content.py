"""Content record — the central entity flowing through the pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin, _uuid


class Content(Base, TenantMixin, TimestampMixin):
    __tablename__ = "contents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    persona_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("personas.id"), nullable=False, index=True
    )
    topic_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("topics.id"), default=None
    )

    title: Mapped[str | None] = mapped_column(String(500), default=None)

    # Pipeline outputs
    draft_content: Mapped[str | None] = mapped_column(Text, default=None)
    final_content: Mapped[str | None] = mapped_column(Text, default=None)

    # Generation metadata
    prompt_version: Mapped[str | None] = mapped_column(String(50), default=None)
    model_used: Mapped[str | None] = mapped_column(String(100), default=None)
    generation_tokens: Mapped[int | None] = mapped_column(Integer, default=None)

    # Pipeline state machine:
    # draft → researching → generating → review → approved/rejected
    #   → scheduled → publishing → published → archived
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)

    # Quality
    quality_score: Mapped[float | None] = mapped_column(Float, default=None)
    style_consistency: Mapped[float | None] = mapped_column(Float, default=None)
    quality_issues: Mapped[list[dict[str, Any]] | None] = mapped_column(
        type_=String(2048), default=None
    )

    # Scheduling
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
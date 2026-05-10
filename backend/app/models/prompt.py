"""Prompt template registry — versioned prompts for every task type."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, _uuid


class Prompt(Base):
    __tablename__ = "prompts"
    __table_args__ = (
        UniqueConstraint("persona_id", "task_type", "version", name="uq_prompt_version"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    persona_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("personas.id"), nullable=False, index=True
    )
    task_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # content_generation | topic_ranking | quality_check | ...
    version: Mapped[str] = mapped_column(String(20), nullable=False)

    system_template: Mapped[str | None] = mapped_column(Text, default=None)
    user_template: Mapped[str | None] = mapped_column(Text, default=None)
    variables: Mapped[dict[str, Any] | None] = mapped_column(type_=String(1024), default=None)
    model_config: Mapped[dict[str, Any] | None] = mapped_column(type_=String(1024), default=None)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    performance_score: Mapped[float | None] = mapped_column(Float, default=None)
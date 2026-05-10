"""Persona / style profile — the core differentiation of iPerson.

A persona captures a creator's unique voice, visual style, and narrative
patterns.  It is the central configuration object that drives the entire
content pipeline.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin, _uuid


class Persona(Base, TenantMixin, TimestampMixin):
    __tablename__ = "personas"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="zh")  # zh | en | ja

    # L1: Base prompt modelling (inherited from IPulse)
    system_prompt: Mapped[str | None] = mapped_column(Text, default=None)
    tone_instruction: Mapped[str | None] = mapped_column(Text, default=None)

    # L2: Few-shot style profile
    style_profile: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    few_shot_examples: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, default=None)
    banned_patterns: Mapped[list[str] | None] = mapped_column(JSON, default=None)

    # Visual identity
    visual_theme: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)

    # Content focus
    focus_areas: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    keywords: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    content_types: Mapped[list[str] | None] = mapped_column(JSON, default=None)

    # Quality
    style_consistency_threshold: Mapped[float] = mapped_column(Float, default=0.65)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<Persona {self.name} [{self.language}]>"
"""Discovered topic — sourced from external platforms."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin, _uuid


class Topic(Base, TenantMixin, TimestampMixin):
    __tablename__ = "topics"
    __table_args__ = (UniqueConstraint("source", "source_id", name="uq_topic_source"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, default=None)
    url: Mapped[str | None] = mapped_column(Text, default=None)
    heat_score: Mapped[float | None] = mapped_column(Float, default=None)
    ai_rank_score: Mapped[float | None] = mapped_column(Float, default=None)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(type_=String(2048), default=None)
    title_hash: Mapped[str | None] = mapped_column(String(64), default=None, index=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=None
    )
"""Content version history — tracks every edit for audit & rollback."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, _uuid


class ContentVersion(Base):
    """Immutable snapshot of content at each modification."""

    __tablename__ = "content_versions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    content_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("contents.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content_text: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[str | None] = mapped_column(String(30), default=None)
    changed_by: Mapped[str | None] = mapped_column(String(100), default=None)
    change_reason: Mapped[str | None] = mapped_column(String(500), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
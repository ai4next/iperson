"""Publication record — tracks every platform push."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, _uuid


class Publication(Base):
    __tablename__ = "publications"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    content_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("contents.id"), nullable=False, index=True
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    platform_post_id: Mapped[str | None] = mapped_column(String(255), default=None)
    platform_url: Mapped[str | None] = mapped_column(Text, default=None)

    status: Mapped[str] = mapped_column(String(30), default="pending")
    # pending | publishing | published | failed | deleted

    error_message: Mapped[str | None] = mapped_column(Text, default=None)
    publish_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        type_=String(2048), default=None
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
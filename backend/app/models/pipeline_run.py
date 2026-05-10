"""Pipeline run log — execution audit trail with checkpoint support."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, _uuid


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    tenant_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("tenants.id"), default=None
    )
    persona_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("personas.id"), default=None
    )
    content_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("contents.id"), default=None
    )

    status: Mapped[str] = mapped_column(String(30), default="running")
    stages_completed: Mapped[list[dict[str, Any]] | None] = mapped_column(
        type_=String(4096), default=None
    )
    errors: Mapped[list[dict[str, Any]] | None] = mapped_column(
        type_=String(4096), default=None
    )
    context_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        type_=String(8192), default=None
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
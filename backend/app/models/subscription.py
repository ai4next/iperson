"""Subscription & billing model (Phase 2)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, _uuid


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_tenant_subscription"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("tenants.id"), nullable=False
    )
    plan_tier: Mapped[str] = mapped_column(String(50), default="free")  # free | pro | enterprise
    status: Mapped[str] = mapped_column(
        String(20), default="trialing"
    )  # active | trialing | past_due | canceled
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    payment_provider: Mapped[str | None] = mapped_column(
        String(50), default=None
    )  # stripe | alipay | wechat
    provider_subscription_id: Mapped[str | None] = mapped_column(String(255), default=None)
"""Platform account — stores OAuth credentials per social platform."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Boolean, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, TimestampMixin, _uuid


class PlatformAccount(Base, TenantMixin, TimestampMixin):
    """Bound social-media account for a tenant.

    Stores encrypted OAuth tokens so the publish hub can authenticate
    on behalf of the user without re-authorization each time.
    """

    __tablename__ = "platform_accounts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "platform", name="uq_tenant_platform"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # xiaohongshu | weibo | wechat | twitter | douyin | zhihu

    account_name: Mapped[str | None] = mapped_column(String(255), default=None)
    account_id: Mapped[str | None] = mapped_column(String(255), default=None)

    # OAuth credentials (encrypted at rest in production)
    access_token: Mapped[str | None] = mapped_column(Text, default=None)
    refresh_token: Mapped[str | None] = mapped_column(Text, default=None)
    token_expires_at: Mapped[str | None] = mapped_column(String(50), default=None)

    # Platform-specific config
    extra_config: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
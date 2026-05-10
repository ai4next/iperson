"""User model — belongs to a tenant."""

from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, _uuid


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    tenant_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("tenants.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="editor")  # owner | admin | editor | viewer
    avatar_url: Mapped[str | None] = mapped_column(String(2048), default=None)
    password_hash: Mapped[str | None] = mapped_column(String(255), default=None)
    oauth_provider: Mapped[str | None] = mapped_column(String(50), default=None)
    oauth_id: Mapped[str | None] = mapped_column(String(255), default=None)
    is_active: Mapped[bool] = mapped_column(default=True)

    # relationships
    tenant = relationship("Tenant", back_populates="users")
"""Tenant / workspace model."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, _uuid

if TYPE_CHECKING:
    from app.models.user import User


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    plan_tier: Mapped[str] = mapped_column(String(50), default="free")  # free | pro | enterprise
    settings: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)

    # relationships
    users: Mapped[list[User]] = relationship("User", back_populates="tenant", lazy="selectin")
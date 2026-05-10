"""Tenant-aware request context & middleware helpers."""

from __future__ import annotations

import contextvars
from typing import TYPE_CHECKING

tenant_context_var: contextvars.ContextVar[str] = contextvars.ContextVar("tenant_id")

if TYPE_CHECKING:
    from app.models.tenant import Tenant


def set_current_tenant_id(tenant_id: str) -> None:
    tenant_context_var.set(tenant_id)


def get_current_tenant_id() -> str | None:
    return tenant_context_var.get(None)


def inject_tenant_filter(statement, tenant_id: str | None = None):
    """Append a tenant_id filter to a SQLAlchemy select/update/delete statement.

    Every domain model that carries ``tenant_id`` should use this helper so
    that cross-tenant leakage is prevented at the query layer.
    """
    tid = tenant_id or get_current_tenant_id()
    if tid is None:
        return statement
    return statement.where(
        # The caller is responsible for ensuring the target model has tenant_id
        statement.table().c.tenant_id == tid  # type: ignore[union-attr]
    )
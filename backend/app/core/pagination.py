"""Shared pagination utility for API list endpoints."""

from __future__ import annotations

from math import ceil

from fastapi import Query
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


def pagination_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """FastAPI dependency: returns (page, page_size, offset)."""
    return page, page_size, (page - 1) * page_size


async def paginate(
    db: AsyncSession,
    query: Select,
    page: int,
    page_size: int,
):
    """Apply pagination to a query and return (items, total_count)."""
    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(query)).scalars().all()

    return items, total


def paginated_response(items: list, total: int, page: int, page_size: int) -> dict:
    """Build a paginated API response dict."""
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, ceil(total / page_size)),
    }
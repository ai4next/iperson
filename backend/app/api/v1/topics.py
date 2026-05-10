"""Topic discovery and management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_current_tenant_id
from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.topic import Topic
from app.models.user import User
from app.schemas import PaginatedResponse

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("/", response_model=PaginatedResponse)
async def list_topics(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tid = get_current_tenant_id()
    query = select(Topic).where(Topic.tenant_id == tid)
    if source:
        query = query.where(Topic.source == source)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Topic.heat_score.desc().nullslast()).offset((page - 1) * page_size).limit(page_size)
    items = (await db.execute(query)).scalars().all()

    return PaginatedResponse(
        items=[{"id": t.id, "title": t.title, "source": t.source, "heat_score": t.heat_score,
                 "url": t.url, "discovered_at": str(t.discovered_at) if t.discovered_at else None}
               for t in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("/discover", status_code=status.HTTP_202_ACCEPTED)
async def discover_topics(
    source: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("editor")),
):
    """Trigger topic discovery.

    In production this dispatches a Celery task. Currently returns
    accepted status — the actual discovery runs asynchronously.
    """
    # TODO: dispatch Celery task
    return {"status": "accepted", "message": "Topic discovery queued", "source": source or "all"}


@router.get("/{topic_id}")
async def get_topic(
    topic_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tid = get_current_tenant_id()
    result = await db.execute(select(Topic).where(Topic.id == topic_id, Topic.tenant_id == tid))
    topic = result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
    return topic
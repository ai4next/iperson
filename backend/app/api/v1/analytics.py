"""Analytics and reporting endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenant import get_current_tenant_id
from app.database import get_db
from app.dependencies import get_current_user
from app.models.content import Content
from app.models.metrics import Metric
from app.models.publication import Publication
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def dashboard(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Aggregate dashboard metrics for the current tenant."""
    tid = get_current_tenant_id()

    # Published content count
    result = await db.execute(
        select(func.count()).select_from(Content).where(
            Content.tenant_id == tid,
            Content.status == "published",
        )
    )
    total_published = result.scalar() or 0

    # Draft content count
    result = await db.execute(
        select(func.count()).select_from(Content).where(
            Content.tenant_id == tid,
            Content.status == "draft",
        )
    )
    total_drafts = result.scalar() or 0

    # Platform distribution
    result = await db.execute(
        select(Publication.platform, func.count(Publication.id))
        .select_from(Publication)
        .join(Content, Publication.content_id == Content.id)
        .where(Content.tenant_id == tid)
        .group_by(Publication.platform)
    )
    platform_dist = dict(result.all())

    # Total likes
    result = await db.execute(
        select(func.coalesce(func.sum(Metric.likes), 0))
        .select_from(Metric)
        .join(Publication, Metric.publication_id == Publication.id)
        .join(Content, Publication.content_id == Content.id)
        .where(Content.tenant_id == tid)
    )
    total_likes = result.scalar() or 0

    return {
        "total_published": total_published,
        "total_drafts": total_drafts,
        "platform_distribution": platform_dist,
        "total_likes": total_likes,
        "period_days": days,
    }


@router.get("/contents/{content_id}")
async def content_analytics(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Per-content analytics with time-series metrics."""
    tid = get_current_tenant_id()

    # Verify content belongs to tenant
    result = await db.execute(
        select(Content).where(Content.id == content_id, Content.tenant_id == tid)
    )
    content = result.scalar_one_or_none()
    if content is None:
        return {"error": "Content not found"}

    # Get publications for this content
    pubs_result = await db.execute(
        select(Publication).where(Publication.content_id == content_id)
    )
    publications = pubs_result.scalars().all()

    # Get metrics per publication
    all_metrics = []
    for pub in publications:
        m_result = await db.execute(
            select(Metric).where(Metric.publication_id == pub.id).order_by(Metric.collected_at)
        )
        metrics = m_result.scalars().all()
        all_metrics.append({
            "platform": pub.platform,
            "post_id": pub.platform_post_id,
            "url": pub.platform_url,
            "published_at": str(pub.published_at) if pub.published_at else None,
            "metrics": [{"collected_at": str(m.collected_at), "likes": m.likes,
                        "comments": m.comments, "shares": m.shares, "views": m.views}
                       for m in metrics],
        })

    return {
        "content_id": content_id,
        "title": content.title,
        "status": content.status,
        "publications": all_metrics,
    }


@router.get("/report")
async def report(
    period: str = Query("weekly", regex="^(weekly|monthly)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Generate a period performance report."""
    # TODO: wire up AnalyticsService.generate_weekly_report()
    return {
        "period": period,
        "status": "Report generation queued",
        "note": "Production implementation will generate and cache reports asynchronously.",
    }
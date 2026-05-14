from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass
class ContentMetrics:
    content_id: str
    platform: str
    views: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    collected_at: str = ""


class AnalyticsEngine:
    """Tracks and analyzes content performance metrics."""

    def collect_metrics(
        self,
        content_id: str,
        platform: str,
        views: int = 0,
        likes: int = 0,
        shares: int = 0,
        comments: int = 0,
    ) -> ContentMetrics:
        """Record content performance metrics."""
        from iperson.storage.db import get_connection

        metrics = ContentMetrics(
            content_id=content_id,
            platform=platform,
            views=views,
            likes=likes,
            shares=shares,
            comments=comments,
            collected_at=datetime.now(timezone.utc).isoformat(),
        )
        conn = get_connection()
        try:
            conn.execute(
                "INSERT INTO content_metrics (id, content_id, platform, views, likes, shares, comments, collected_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    uuid.uuid4().hex,
                    metrics.content_id,
                    metrics.platform,
                    metrics.views,
                    metrics.likes,
                    metrics.shares,
                    metrics.comments,
                    metrics.collected_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return metrics

    def get_metrics(self, content_id: str) -> list[dict[str, Any]]:
        """Get all metrics for a content_id."""
        from iperson.storage.db import get_connection

        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT platform, views, likes, shares, comments, collected_at FROM content_metrics WHERE content_id = ? ORDER BY collected_at DESC",
                (content_id,),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_summary(self, content_id: str) -> dict[str, Any]:
        """Get aggregated metrics summary for a content_id."""
        from iperson.storage.db import get_connection

        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT COALESCE(SUM(views), 0) as total_views, COALESCE(SUM(likes), 0) as total_likes, COALESCE(SUM(shares), 0) as total_shares, COALESCE(SUM(comments), 0) as total_comments, COUNT(DISTINCT platform) as platforms FROM content_metrics WHERE content_id = ?",
                (content_id,),
            ).fetchone()
            return dict(row)
        finally:
            conn.close()
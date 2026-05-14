from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any


@dataclass
class TopicSuggestion:
    topic: str
    source: str  # "kb", "trending", "analytics"
    score: float
    reason: str


class TopicSuggestionEngine:
    """Suggests content topics based on KB content, analytics, and trends."""

    def suggest_from_kb(self, top_n: int = 5) -> list[TopicSuggestion]:
        """Suggest topics by extracting key themes from knowledge base."""
        from iperson.storage.db import get_connection
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT title, content FROM kb_docs ORDER BY RANDOM() LIMIT ?",
                (top_n * 3,),
            ).fetchall()
        finally:
            conn.close()

        suggestions = []
        for row in rows[:top_n]:
            title = row["title"] or row["content"][:50]
            suggestions.append(TopicSuggestion(
                topic=title,
                source="kb",
                score=0.7,
                reason="基于知识库内容推荐",
            ))
        return suggestions

    def suggest_from_analytics(self, top_n: int = 5) -> list[TopicSuggestion]:
        """Suggest topics based on what performed well."""
        from iperson.storage.db import get_connection
        conn = get_connection()
        try:
            rows = conn.execute("""
                SELECT c.topic, SUM(m.views) as total_views, SUM(m.likes) as total_likes
                FROM content_metrics m
                JOIN contents c ON c.id = m.content_id
                GROUP BY c.topic
                ORDER BY total_views DESC
                LIMIT ?
            """, (top_n,)).fetchall()
        finally:
            conn.close()

        return [TopicSuggestion(
            topic=row["topic"],
            source="analytics",
            score=min(1.0, (row["total_views"] or 0) / 1000 + (row["total_likes"] or 0) / 100),
            reason=f"历史表现: {row['total_views'] or 0}阅读, {row['total_likes'] or 0}点赞",
        ) for row in rows]

    def suggest_all(self, top_n: int = 5) -> list[TopicSuggestion]:
        """Combine suggestions from all sources."""
        kb = self.suggest_from_kb(top_n)
        analytics = self.suggest_from_analytics(top_n)
        combined = sorted(kb + analytics, key=lambda s: s.score, reverse=True)
        return combined[:top_n]
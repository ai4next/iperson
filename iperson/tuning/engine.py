from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TuningSuggestion:
    dimension: str
    current_value: str
    suggested_value: str
    reason: str
    confidence: float


class StyleTuningEngine:
    """Analyzes content performance and suggests persona style adjustments."""

    def suggest_style_adjustments(self, persona_name: str) -> list[TuningSuggestion]:
        """Suggest style adjustments based on content performance."""
        from iperson.storage.db import get_connection

        suggestions = []
        conn = get_connection()
        try:
            # Find content with low engagement per persona
            rows = conn.execute("""
                SELECT c.id, c.topic, m.views, m.likes
                FROM contents c
                JOIN content_metrics m ON m.content_id = c.id
                WHERE c.persona_name = ?
                ORDER BY m.views ASC
                LIMIT 5
            """, (persona_name,)).fetchall()
        finally:
            conn.close()

        if rows:
            low_engagement = sum(1 for r in rows if (r["likes"] or 0) < 10)
            if low_engagement > 3:
                suggestions.append(TuningSuggestion(
                    dimension="tone_instruction",
                    current_value="当前语气指令",
                    suggested_value="增加互动性和亲和力",
                    reason=f"最近{len(rows)}篇内容中{low_engagement}篇互动率低，建议调整语气",
                    confidence=0.6,
                ))

        return suggestions
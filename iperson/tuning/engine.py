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

    def analyze_banned_patterns(self, persona_name: str) -> list[TuningSuggestion]:
        """Analyze which banned patterns are being triggered most."""
        from iperson.storage.db import get_connection
        conn = get_connection()
        try:
            persona = conn.execute(
                "SELECT id, banned_patterns FROM personas WHERE name = ?",
                (persona_name,),
            ).fetchone()
        finally:
            conn.close()

        if not persona:
            return []

        import json
        banned = json.loads(persona["banned_patterns"]) if isinstance(persona["banned_patterns"], str) else persona["banned_patterns"] or []

        suggestions = []
        from iperson.core.humanizer.detector import AIDetector
        detector = AIDetector()

        # Check for patterns that appear too often in generated content
        conn = get_connection()
        try:
            rows = conn.execute(
                "SELECT draft_content FROM contents WHERE persona_id = (SELECT id FROM personas WHERE name = ?) ORDER BY created_at DESC LIMIT 10",
                (persona_name,),
            ).fetchall()
        finally:
            conn.close()

        if not rows:
            return suggestions

        combined = " ".join(r["draft_content"] or "" for r in rows)
        matches = detector.detect(combined)

        # Group by category
        from collections import Counter
        cat_counts = Counter(m.category for m in matches)

        for cat, count in cat_counts.most_common(3):
            confidence = min(1.0, count / 5)
            suggestions.append(TuningSuggestion(
                dimension=f"ai_pattern_{cat}",
                current_value=f"出现{count}次",
                suggested_value=f"减少{cat}类AI表达",
                reason=f"生成内容中{cat}类AI模式出现{count}次，建议加入禁用词列表",
                confidence=confidence,
            ))

        return suggestions

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
                WHERE c.persona_id = (SELECT id FROM personas WHERE name = ?)
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
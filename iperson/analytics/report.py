from __future__ import annotations

from typing import Any


def format_summary(summary: dict[str, Any]) -> str:
    lines = [
        "\U0001f4ca 内容表现分析",
        f"  总阅读: {summary.get('total_views', 0)}",
        f"  总点赞: {summary.get('total_likes', 0)}",
        f"  总分享: {summary.get('total_shares', 0)}",
        f"  总评论: {summary.get('total_comments', 0)}",
        f"  覆盖平台: {summary.get('platforms', 0)}",
    ]
    return "\n".join(lines)
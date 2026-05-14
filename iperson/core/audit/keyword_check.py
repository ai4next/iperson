from __future__ import annotations


# Default banned and sensitive word lists
BANNED_WORDS: list[str] = [
    "总的来说", "综上所述", "总而言之", "首先", "其次", "最后",
    "值得注意的是", "需要指出的是", "不可否认", "毋庸置疑",
]

SENSITIVE_WORDS: list[str] = [
    "绝对", "一定", "必须", "最", "第一", "唯一",
    "百分之百", "永远", "完全", "所有",
]


def check_keyword_fit(content: str, config: dict | None = None) -> dict:
    """Check content for keyword compliance with sub-dimension scores.

    The function checks against built-in banned and sensitive word lists,
    optionally overridden by config.

    Args:
        content: The text to check.
        config: Optional dict with keys:
            - banned_words: list[str] override
            - sensitive_words: list[str] override

    Returns:
        A dict with:
            - score: float (0.0-1.0) composite score
            - sub_scores: dict of sub-dimension scores
            - details: dict with banned_found and sensitive_found lists
            - suggestions: list of improvement suggestions
    """
    banned_words = (
        config.get("banned_words", BANNED_WORDS) if config else BANNED_WORDS
    )
    sensitive_words = (
        config.get("sensitive_words", SENSITIVE_WORDS) if config else SENSITIVE_WORDS
    )

    content_lower = content.lower()

    # Sub-dimension: banned word ratio
    banned_found = [w for w in banned_words if w.lower() in content_lower]
    banned_score = max(0.0, 1.0 - len(banned_found) / max(len(banned_words), 1))

    # Sub-dimension: sensitive word ratio
    sensitive_found = [
        w for w in sensitive_words if w.lower() in content_lower
    ]
    sensitive_score = (
        max(0.0, 1.0 - len(sensitive_found) / max(len(sensitive_words), 1))
        if sensitive_words
        else 1.0
    )

    score = (banned_score + sensitive_score) / 2.0

    suggestions: list[str] = []
    if banned_found:
        suggestions.append(f"禁用词使用: {', '.join(banned_found[:3])}")
    if sensitive_found:
        suggestions.append(f"敏感词使用: {', '.join(sensitive_found[:3])}")

    return {
        "score": score,
        "sub_scores": {
            "banned_word_ratio": banned_score,
            "sensitive_word_ratio": sensitive_score,
        },
        "details": {
            "banned_found": banned_found,
            "sensitive_found": sensitive_found,
        },
        "suggestions": suggestions,
    }
from __future__ import annotations

PLATFORM_RULES: dict[str, dict] = {
    "xiaohongshu": {"max_chars": 1000, "min_chars": 50, "min_images": 1},
    "wechat": {"max_chars": 50000, "min_chars": 200},
    "zhihu": {"max_chars": 30000, "min_chars": 100},
}


def check_platform_rules(content: str, platform: str) -> dict:
    """Check content against platform-specific constraints.

    Validates character count against the target platform's limits.

    Args:
        content: The text to check.
        platform: Target platform name (e.g., "xiaohongshu", "wechat", "zhihu").

    Returns:
        A dict with:
            - score: float (0.0-1.0)
            - status: "pass" | "review" | "fail"
            - platform: str
            - char_count: int
            - max_chars: int | None
            - issues: list[str]
    """
    rules = PLATFORM_RULES.get(platform)
    char_count = len(content)
    issues: list[str] = []

    if rules is None:
        return {
            "score": 1.0,
            "status": "pass",
            "platform": platform,
            "char_count": char_count,
            "max_chars": None,
            "issues": [],
        }

    max_chars = rules["max_chars"]
    min_chars = rules.get("min_chars", 0)

    if char_count > max_chars:
        issues.append(
            f"Content exceeds max {max_chars} chars ({char_count} chars)"
        )
    if char_count < min_chars:
        issues.append(
            f"Content below min {min_chars} chars ({char_count} chars)"
        )

    if not issues:
        score = 1.0
        status = "pass"
    else:
        # Proportional penalty based on deviation from limits
        penalty = 0.0
        if char_count > max_chars:
            penalty = min((char_count - max_chars) / max_chars, 0.5)
        if char_count < min_chars:
            penalty = min((min_chars - char_count) / min_chars, 0.5)
        score = max(1.0 - penalty, 0.0)

        if score >= 0.7:
            status = "review"
        else:
            status = "fail"

    return {
        "score": score,
        "status": status,
        "platform": platform,
        "char_count": char_count,
        "max_chars": max_chars,
        "issues": issues,
    }
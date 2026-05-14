from __future__ import annotations


def check_keyword_fit(
    content: str,
    keywords: list[str],
    primary_keywords: list[str] | None = None,
) -> dict:
    """Check keyword presence in content.

    Verifies that primary keywords appear in the title (first line), body,
    and the first 200 characters of the content.

    Args:
        content: The text to check.
        keywords: Full list of keywords.
        primary_keywords: Subset of critical keywords. If None, all keywords
            are treated as primary.

    Returns:
        A dict with:
            - score: float (0.0-1.0)
            - status: "pass" | "review" | "fail"
            - primary_keywords: list[str]
            - keyword_in_title: bool
            - keyword_in_body: bool
            - checks: dict per-keyword detail
    """
    if not keywords:
        return {
            "score": 1.0,
            "status": "pass",
            "primary_keywords": [],
            "keyword_in_title": False,
            "keyword_in_body": False,
            "checks": {},
        }

    primary = primary_keywords if primary_keywords else keywords
    lines = content.strip().split("\n")
    title = lines[0] if lines else ""
    body = "\n".join(lines[1:]) if len(lines) > 1 else ""
    first_200 = content[:200]

    checks: dict[str, dict] = {}
    hits = 0

    for kw in primary:
        in_title = kw in title
        in_body = kw in body
        in_first_200 = kw in first_200
        found = in_title or in_body
        if found:
            hits += 1
        checks[kw] = {
            "in_title": in_title,
            "in_body": in_body,
            "in_first_200": in_first_200,
            "found": found,
        }

    score = hits / max(len(primary), 1)

    keyword_in_title = any(checks[kw]["in_title"] for kw in primary)
    keyword_in_body = any(checks[kw]["in_body"] for kw in primary)

    if score >= 0.8:
        status = "pass"
    elif score >= 0.3:
        status = "review"
    else:
        status = "fail"

    return {
        "score": score,
        "status": status,
        "primary_keywords": primary,
        "keyword_in_title": keyword_in_title,
        "keyword_in_body": keyword_in_body,
        "checks": checks,
    }
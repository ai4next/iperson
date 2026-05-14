from __future__ import annotations

import re


def check_structure(content: str) -> dict:
    """Analyze document structure quality.

    Checks for the presence of markdown headings (H1, H2, H3), lists,
    and evaluates paragraph count adequacy.

    Scoring weights:
        - H1: 0.3
        - H2: 0.25
        - H3: 0.15
        - List: 0.1
        - Proper paragraph count (>= 2): 0.2

    Args:
        content: The text to analyze.

    Returns:
        A dict with:
            - score: float (0.0-1.0)
            - status: "pass" | "review" | "fail"
            - has_h1: bool
            - has_h2: bool
            - has_h3: bool
            - has_list: bool
            - paragraph_count: int
    """
    lines = content.strip().split("\n")

    has_h1 = any(line.startswith("# ") for line in lines if line.strip())
    has_h2 = any(line.startswith("## ") for line in lines if line.strip())
    has_h3 = any(line.startswith("### ") for line in lines if line.strip())

    # Detect lists: numbered (1. ) or bullet (-, *)
    has_list = any(
        bool(re.match(r"^\s*(?:\d+\.\s|[-*]\s)", line))
        for line in lines
        if line.strip()
    )

    # Count non-empty paragraphs (separated by blank lines)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", content) if p.strip()]
    paragraph_count = len(paragraphs)

    # Calculate score
    score = 0.0
    if has_h1:
        score += 0.3
    if has_h2:
        score += 0.25
    if has_h3:
        score += 0.15
    if has_list:
        score += 0.1
    if paragraph_count >= 2:
        score += 0.2

    score = min(score, 1.0)

    if score >= 0.7:
        status = "pass"
    elif score >= 0.3:
        status = "review"
    else:
        status = "fail"

    return {
        "score": score,
        "status": status,
        "has_h1": has_h1,
        "has_h2": has_h2,
        "has_h3": has_h3,
        "has_list": has_list,
        "paragraph_count": paragraph_count,
    }
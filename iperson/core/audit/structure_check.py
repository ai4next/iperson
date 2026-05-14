from __future__ import annotations


def check_structure(content: str, config: dict | None = None) -> dict:
    """Analyze document structure quality with sub-dimension scores.

    Evaluates heading hierarchy, paragraph length distribution, and logical
    flow via transition words.

    Args:
        content: The text to analyze.
        config: Optional dict (reserved for future use).

    Returns:
        A dict with:
            - score: float (0.0-1.0) composite score
            - sub_scores: dict of sub-dimension scores
                - heading_hierarchy: float
                - paragraph_length_distribution: float
                - logical_flow_score: float
            - suggestions: list of improvement suggestions
    """
    lines = content.split("\n")
    headings = [l for l in lines if l.strip().startswith("#")]
    has_h1 = any(l.strip().startswith("# ") for l in lines)

    # Sub-dimension: heading hierarchy
    heading_score = 1.0
    if headings and not has_h1:
        heading_score -= 0.3
    if not headings:
        heading_score = 0.3
    heading_score = max(0.0, heading_score)

    # Sub-dimension: paragraph length distribution
    paragraphs = [
        l for l in lines if l.strip() and not l.strip().startswith("#")
    ]
    if paragraphs:
        lengths = [len(p) for p in paragraphs]
        long_ratio = sum(1 for l in lengths if l > 500) / len(lengths)
        short_ratio = sum(1 for l in lengths if l < 10) / len(lengths)
        para_score = max(0.0, 1.0 - long_ratio - short_ratio * 0.5)
    else:
        para_score = 0.5

    # Sub-dimension: logical flow via transition words
    transition_words = [
        "因为", "所以", "但是", "然而", "而且", "此外",
        "如果", "虽然", "因此", "例如",
    ]
    transition_count = sum(1 for w in transition_words if w in content)
    flow_score = min(1.0, transition_count / 5.0)

    score = (heading_score + para_score + flow_score) / 3.0

    suggestions: list[str] = []
    if not headings:
        suggestions.append("文档缺少标题结构")
    elif not has_h1:
        suggestions.append("缺少一级标题")
    if flow_score < 0.5:
        suggestions.append("逻辑衔接词使用较少，段落间连贯性可加强")

    return {
        "score": score,
        "sub_scores": {
            "heading_hierarchy": heading_score,
            "paragraph_length_distribution": para_score,
            "logical_flow_score": flow_score,
        },
        "suggestions": suggestions,
    }
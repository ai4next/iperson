from __future__ import annotations

import math
from typing import Any

AI_PHRASES: list[str] = [
    "值得注意的是",
    "总的来说",
    "综上所述",
    "毋庸置疑",
    "不言而喻",
    "显而易见",
    "值得一提的是",
    "不可否认",
    "从这个角度来看",
    "在某种程度",
    "不仅...而且",
    "我们需要",
    "我们可以",
    "让我们",
    "作为一家",
]


def detect_ai_patterns(text: str) -> list[dict[str, Any]]:
    """Detect AI writing patterns in the given text.

    Checks for:
    - AI phrase presence
    - Sequential structure markers (首先, 其次, 最后, 第一, 第二, 第三)
    - Paragraph uniformity (standard deviation of paragraph lengths)

    Args:
        text: The input text to analyze.

    Returns:
        A list of detection results, each with keys:
        - "type": "ai_phrase" | "ai_structure" | "uniform_structure"
        - "phrase" or "pattern" or "detail": the specific item detected
        - "severity": "low" | "medium"
    """
    if not text:
        return []

    findings: list[dict[str, Any]] = []

    # Signal 1: AI phrase detection
    for phrase in AI_PHRASES:
        if phrase in text:
            # Check if it's the exact phrase or a variant
            if "..." in phrase:
                # For patterns like "不仅...而且", check both parts
                parts = phrase.split("...")
                if len(parts) == 2 and parts[0] in text and parts[1] in text:
                    findings.append({
                        "type": "ai_phrase",
                        "phrase": phrase,
                        "severity": "medium",
                    })
            else:
                findings.append({
                    "type": "ai_phrase",
                    "phrase": phrase,
                    "severity": "low",
                })

    # Signal 2: Sequential structure markers
    sequential_markers = ["首先", "其次", "最后", "第一", "第二", "第三"]
    found_markers = [m for m in sequential_markers if m in text]
    if len(found_markers) >= 2:
        findings.append({
            "type": "ai_structure",
            "pattern": "sequential_markers",
            "detail": ", ".join(found_markers),
            "severity": "medium",
        })

    # Signal 3: Paragraph uniformity
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if len(paragraphs) >= 3:
        lengths = [len(p) for p in paragraphs]
        mean_length = sum(lengths) / len(lengths)
        if mean_length > 0:
            variance = sum((p - mean_length) ** 2 for p in lengths) / len(lengths)
            std_dev = math.sqrt(variance)
            # If std dev is less than 30% of the mean, paragraphs are very uniform
            if std_dev / mean_length < 0.3:
                findings.append({
                    "type": "uniform_structure",
                    "detail": f"std_dev={std_dev:.1f}, mean={mean_length:.1f}, "
                    f"ratio={std_dev / mean_length:.2f}",
                    "severity": "low",
                })

    return findings

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class AIPatternMatch:
    category: str
    pattern_name: str
    matched_text: str
    position: tuple[int, int]  # (start, end)
    confidence: float


PATTERN_WEIGHTS: dict[str, float] = {
    "template_openings": 0.25,
    "template_closings": 0.20,
    "over修饰": 0.20,
    "verbose_transitions": 0.15,
    "mechanical_listing": 0.20,
}

PATTERNS: list[dict[str, Any]] = [
    {"category": "template_openings", "weight": 0.25, "patterns": [
        r"在这个[一-鿿]+的[时\b]",
        r"随着[互联网\w]+的[发展普及]",
        r"在当今[社会时代]",
        r"近年来[，,]\s*",
        r"当[我们你]谈论",
    ]},
    {"category": "template_closings", "weight": 0.20, "patterns": [
        r"总[的之]来说",
        r"让我们[一起共同]",
        r"希望对[你大家]",
        r"[如果只要]你[觉得认为]",
        r"[欢迎期待]你的[留言反馈分享]",
    ]},
    {"category": "over修饰", "weight": 0.20, "patterns": [
        r"无疑[，,]",
        r"至关[重要重]",
        r"极其[重要重]",
        r"非常[重要关键]",
        r"不可[忽视或缺]",
    ]},
    {"category": "verbose_transitions", "weight": 0.15, "patterns": [
        r"[值得需要]注意[的]?是",
        r"[值得需要]一[提说]的是",
        r"需要[特别额外]?指出",
        r"不得不[说提]",
        r"[相对相比]而言",
    ]},
    {"category": "mechanical_listing", "weight": 0.20, "patterns": [
        r"首先[，,]\s*",
        r"其[次二][，,]\s*",
        r"再[次者][，,]\s*",
        r"最[后终][，,]\s*",
        r"第[一二三四五六七八九十][，,]\s*",
    ]},
]


class AIDetector:
    """Detects AI-generated text patterns in content."""

    def __init__(self) -> None:
        self._compiled: list[dict[str, Any]] = []
        for cat in PATTERNS:
            compiled_patterns = [re.compile(p) for p in cat["patterns"]]
            self._compiled.append({
                "category": cat["category"],
                "weight": cat["weight"],
                "patterns": compiled_patterns,
            })

    def detect(self, content: str) -> list[AIPatternMatch]:
        """Scan content and return all AI pattern matches with details."""
        matches: list[AIPatternMatch] = []
        for cat in self._compiled:
            for pattern in cat["patterns"]:
                for m in pattern.finditer(content):
                    matches.append(AIPatternMatch(
                        category=cat["category"],
                        pattern_name=cat["category"],
                        matched_text=m.group(),
                        position=(m.start(), m.end()),
                        confidence=0.8,
                    ))
        return matches

    def detect_by_category(self, content: str) -> dict[str, list[AIPatternMatch]]:
        """Group matches by category."""
        all_matches = self.detect(content)
        result: dict[str, list[AIPatternMatch]] = {}
        for m in all_matches:
            result.setdefault(m.category, []).append(m)
        return result


# Backward-compatible exports

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
    """Detect AI writing patterns in the given text. (legacy API)"""
    if not text:
        return []

    findings: list[dict[str, Any]] = []

    # Signal 1: AI phrase detection
    for phrase in AI_PHRASES:
        if phrase in text:
            if "..." in phrase:
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
            if std_dev / mean_length < 0.3:
                findings.append({
                    "type": "uniform_structure",
                    "detail": f"std_dev={std_dev:.1f}, mean={mean_length:.1f}, "
                    f"ratio={std_dev / mean_length:.2f}",
                    "severity": "low",
                })

    return findings
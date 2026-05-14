from __future__ import annotations

import math

from iperson.core.humanizer.detector import AIDetector, AI_PHRASES, PATTERN_WEIGHTS


CALIBRATION_FACTOR = 1.2


class AIScorer:
    """Scores content for AI-likeness using weighted pattern analysis."""

    def __init__(self, detector: AIDetector | None = None) -> None:
        self.detector = detector or AIDetector()

    def score(self, content: str) -> float:
        """Compute weighted AI score. Returns 0.0 (natural) to 1.0 (very AI-like)."""
        grouped = self.detector.detect_by_category(content)
        if not grouped:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0
        for category, matches in grouped.items():
            weight = PATTERN_WEIGHTS.get(category, 0.15)
            category_score = min(1.0, len(matches) * 0.4)
            weighted_sum += category_score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        raw_score = weighted_sum / total_weight
        return min(1.0, raw_score * CALIBRATION_FACTOR)

    def classify(self, score: float) -> str:
        if score <= 0.25:
            return "low"
        if score <= 0.50:
            return "moderate"
        return "high"

    def should_rewrite(self, score: float, min_score: float = 0.35) -> bool:
        return score > min_score


def score_ai_ness(text: str) -> float:
    """Score how AI-like the given text reads. (legacy API)

    Uses three weighted signals:
    - Signal 1 (40%): AI phrase density -- count of AI_PHRASES hits per ~100 chars
    - Signal 2 (30%): Paragraph uniformity -- penalizes paragraphs with very similar lengths
    - Signal 3 (30%): Sequential markers -- count of 首先/其次/最后/第一/第二/第三

    Args:
        text: The input text to score.

    Returns:
        A float between 0.0 (completely natural) and 1.0 (very AI-like).
    """
    if not text:
        return 0.0

    text_len = len(text)

    # Signal 1: AI phrase density (40%)
    ai_phrase_count = 0
    for phrase in AI_PHRASES:
        if "..." in phrase:
            parts = phrase.split("...")
            if len(parts) == 2 and parts[0] in text and parts[1] in text:
                ai_phrase_count += 1
        else:
            ai_phrase_count += text.count(phrase)

    # Normalize to hits per 100 characters, cap at 1.0
    phrase_density = ai_phrase_count / max(text_len / 100, 1)
    signal_1 = min(phrase_density / 5.0, 1.0)  # 5 hits per 100 chars = max AI

    # Signal 2: Paragraph uniformity (30%)
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    if len(paragraphs) >= 3:
        lengths = [len(p) for p in paragraphs]
        mean_length = sum(lengths) / len(lengths)
        if mean_length > 0:
            variance = sum((p - mean_length) ** 2 for p in lengths) / len(lengths)
            std_dev = math.sqrt(variance)
            ratio = std_dev / mean_length
            # ratio < 0.3 means very uniform -> high AI signal
            # ratio > 1.0 means very diverse -> natural
            if ratio < 0.3:
                signal_2 = 1.0 - (ratio / 0.3) * 0.8  # 1.0 at ratio=0, 0.2 at ratio=0.3
            else:
                signal_2 = max(0.0, 0.2 - ((ratio - 0.3) / 0.7) * 0.2)  # tapers off to 0
        else:
            signal_2 = 0.0
    else:
        signal_2 = 0.0

    # Signal 3: Sequential markers (30%)
    sequential_markers = ["首先", "其次", "最后", "第一", "第二", "第三"]
    marker_count = sum(text.count(m) for m in sequential_markers)
    # Normalize to hits per 100 characters
    marker_density = marker_count / max(text_len / 100, 1)
    signal_3 = min(marker_density / 3.0, 1.0)  # 3 markers per 100 chars = max AI

    # Weighted combination
    score = signal_1 * 0.4 + signal_2 * 0.3 + signal_3 * 0.3

    return round(min(max(score, 0.0), 1.0), 4)
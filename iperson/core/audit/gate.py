from __future__ import annotations

from typing import Any


DEFAULT_WEIGHTS: dict[str, float] = {
    "keyword_fit": 1.0,
    "structure": 1.0,
    "platform_rules": 1.0,
    "ai_score": 1.0,
    "style_consistency": 1.0,
    "grounding": 1.0,
}

DEFAULT_THRESHOLDS: dict[str, float] = {"pass": 0.7, "review": 0.4}


def compute_weighted_score(
    scores: dict[str, float], weights: dict[str, float] | None = None
) -> float:
    """Compute a weighted average of dimension scores."""
    w = weights or DEFAULT_WEIGHTS
    total_weight = 0.0
    weighted_sum = 0.0
    for dim, score in scores.items():
        weight = w.get(dim, 1.0)
        weighted_sum += score * weight
        total_weight += weight
    return weighted_sum / total_weight if total_weight > 0 else 0.0


class AuditGate:
    """Orchestrates quality audit evaluation with weighted scoring.

    Evaluates pre-computed dimension scores against configurable thresholds
    and minimum dimension scores.

    Args:
        config: Optional dict with keys:
            - weights: dict[str, float] per-dimension weights
            - thresholds: dict[str, float] with "pass" and "review" keys
            - min_dimension_score: float, minimum acceptable score per dimension
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.weights = self.config.get("weights", DEFAULT_WEIGHTS)
        self.thresholds = self.config.get("thresholds", DEFAULT_THRESHOLDS)
        self.min_dimension_score = self.config.get("min_dimension_score", 0.0)

    def evaluate(
        self, dimension_scores: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        """Evaluate dimension scores against thresholds.

        Args:
            dimension_scores: dict mapping dimension name to its result dict.
                Each result dict must have at least a "score" key and may
                include "sub_scores", "suggestions", etc.

        Returns:
            A dict with:
                - overall_score: float weighted composite
                - overall_status: "pass" | "review" | "fail"
                - scores: dict of per-dimension scores
                - sub_scores: dict of per-dimension sub_scores
                - suggestions: combined improvement suggestions (max 10)
                - below_min_dimension: list of dimensions below min threshold
        """
        scores: dict[str, float] = {
            dim: data["score"] for dim, data in dimension_scores.items()
        }
        overall_score = compute_weighted_score(scores, self.weights)

        below_min = [
            dim
            for dim, score in scores.items()
            if score < self.min_dimension_score
        ]

        if overall_score >= self.thresholds.get("pass", 0.7) and not below_min:
            overall_status = "pass"
        elif overall_score >= self.thresholds.get("review", 0.4):
            overall_status = "review"
        else:
            overall_status = "fail"

        suggestions: list[str] = []
        for dim, data in dimension_scores.items():
            suggestions.extend(data.get("suggestions", []))

        return {
            "overall_score": overall_score,
            "overall_status": overall_status,
            "scores": scores,
            "sub_scores": {
                dim: data.get("sub_scores", {})
                for dim, data in dimension_scores.items()
            },
            "suggestions": suggestions[:10],
            "below_min_dimension": below_min,
        }


def check_gate(
    scores: dict[str, float],
    thresholds: dict[str, float] | None = None,
    fail_fast: bool = False,
) -> dict[str, Any]:
    """Legacy gate check. Use AuditGate for new code."""
    thresholds = thresholds or {"pass": 0.7, "review": 0.4}
    pass_threshold = thresholds.get("pass", 0.7)
    review_threshold = thresholds.get("review", 0.4)

    overall = sum(scores.values()) / max(len(scores), 1)

    if overall >= pass_threshold:
        status = "pass"
    elif overall >= review_threshold:
        status = "review"
    else:
        status = "fail"

    return {
        "overall_score": overall,
        "overall_status": status,
        "scores": scores,
        "sub_scores": {},
        "suggestions": [],
        "below_min_dimension": [],
    }
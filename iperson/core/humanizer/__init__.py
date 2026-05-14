from __future__ import annotations

from typing import Any

from iperson.core.humanizer.scorer import score_ai_ness
from iperson.core.humanizer.transformer import replace_ai_phrases


async def humanize(
    text: str,
    min_score: float = 0.35,
    max_iterations: int = 2,
) -> dict[str, Any]:
    """Run the full humanization pipeline on the given text.

    Detects AI patterns, transforms them, and scores the result.
    Iterates up to ``max_iterations`` times until the score falls below ``min_score``.

    Args:
        text: The input text to humanize.
        min_score: Score threshold to stop iterating (default 0.35).
        max_iterations: Maximum number of detect-transform-score cycles (default 2).

    Returns:
        A dict with:
        - "text": the humanized text
        - "changes": list of all changes made across iterations
        - "score": the final AI-ness score
        - "iterations": number of iterations performed
    """
    if not text:
        return {"text": text, "changes": [], "score": 0.0, "iterations": 0}

    current_text = text
    all_changes: list[dict[str, Any]] = []
    current_score = score_ai_ness(current_text)
    iterations = 0

    while current_score >= min_score and iterations < max_iterations:
        result = replace_ai_phrases(current_text)
        current_text = result["text"]
        all_changes.extend(result["changes"])
        current_score = score_ai_ness(current_text)
        iterations += 1

    return {
        "text": current_text,
        "changes": all_changes,
        "score": current_score,
        "iterations": iterations,
    }

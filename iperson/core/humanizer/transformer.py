from __future__ import annotations

from typing import Any

from iperson.core.humanizer.detector import AIDetector
from iperson.core.humanizer.scorer import AIScorer


class HumanizerTransformer:
    """Rewrites content to reduce AI痕迹 while preserving information and tone."""

    def __init__(self, detector: AIDetector | None = None, scorer: AIScorer | None = None) -> None:
        self.detector = detector or AIDetector()
        self.scorer = scorer or AIScorer(detector or AIDetector())

    async def transform(self, content: str, config: dict[str, Any] | None = None, llm_client: Any = None, persona_engine: Any = None, stage_config: dict[str, Any] | None = None) -> str:
        cfg = config or {}
        min_score = cfg.get("min_score", 0.35)
        max_iterations = cfg.get("max_iterations", 3)
        focus_regions = cfg.get("focus_regions", True)
        preserve_tone = cfg.get("preserve_tone", True)

        current = content
        iteration = 0

        while iteration < max_iterations:
            score = self.scorer.score(current)
            if score <= min_score:
                break

            if focus_regions:
                matches = self.detector.detect(current)
                markers = self._build_region_markers(matches) if matches else []
            else:
                markers = []

            if llm_client:
                current = await self._rewrite_with_llm(current, markers, llm_client, persona_engine, preserve_tone)
            else:
                current = self._simple_rewrite(current, markers)

            iteration += 1

        return current

    def _build_region_markers(self, matches: list) -> list[dict[str, Any]]:
        markers = []
        for m in matches:
            markers.append({"start": m.position[0], "end": m.position[1], "category": m.category, "matched_text": m.matched_text})
        return markers

    async def _rewrite_with_llm(self, content: str, markers: list[dict[str, Any]], llm_client: Any, persona_engine: Any, preserve_tone: bool) -> str:
        from langchain_core.messages import HumanMessage

        tone_instruction = ""
        if preserve_tone and persona_engine:
            tone_instruction = persona_engine.persona.tone_instruction

        if markers:
            rewrite_regions = "\n".join(f"- Position {m['start']}-{m['end']}: `{m['matched_text']}` (type: {m['category']})" for m in markers)
            prompt = f"Rewrite the following text to make it sound more natural and human-written.\nKeep all factual information unchanged.\nSpecific regions with AI patterns:\n{rewrite_regions}\n\n"
        else:
            prompt = "Rewrite the following text to make it sound more natural and human-written:\n\n"

        if tone_instruction:
            prompt += f"Tone to maintain: {tone_instruction}\n\n"

        prompt += content
        response = await llm_client.ainvoke([HumanMessage(content=prompt)])
        result = response.content
        return result if isinstance(result, str) else content

    def _simple_rewrite(self, content: str, markers: list[dict[str, Any]]) -> str:
        replacements = {"总的来说": "", "值得注意的是": "另外", "首先，": "", "其次，": "", "最后，": ""}
        result = content
        for m in markers:
            for old, new in replacements.items():
                if old in result:
                    result = result.replace(old, new, 1)
                    break
        return result


# Ordered list of (old, new) replacement pairs.
# Order matters -- more specific/longer matches should come first.
REPLACEMENTS: list[tuple[str, str]] = [
    ("值得注意的是，", "其实"),
    ("值得注意的是 ", "有意思的是 "),
    ("总的来说，", "简单来说"),
    ("总的来说 ", "简单来说 "),
    ("综上所述，", "所以"),
    ("综上所述 ", "所以 "),
    ("毋庸置疑，", "毫无疑问"),
    ("不言而喻，", "很明显"),
    ("显而易见，", "很明显"),
    ("值得一提的是，", "对了"),
    ("不可否认，", "说实话"),
    ("从这个角度来看", "换个角度"),
    ("首先，", ""),
    ("其次，", ""),
    ("最后，", ""),
]


def replace_ai_phrases(text: str) -> dict[str, Any]:
    """Replace known AI phrases in the text with more natural alternatives. (legacy API)

    Args:
        text: The input text to transform.

    Returns:
        A dict with:
        - "text": the modified text
        - "changes": list of {"from": str, "to": str, "count": int} for each replacement applied
    """
    changes: list[dict[str, Any]] = []
    modified = text

    for old, new in REPLACEMENTS:
        if old in modified:
            count = modified.count(old)
            modified = modified.replace(old, new)
            changes.append({
                "from": old,
                "to": new,
                "count": count,
            })

    return {
        "text": modified,
        "changes": changes,
    }
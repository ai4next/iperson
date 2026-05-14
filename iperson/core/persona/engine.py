from __future__ import annotations

import re
from typing import Any

from iperson.core.persona.profile import PersonaProfile


class PersonaEngine:
    """Builds prompts and checks style consistency for a given persona."""

    def __init__(self, persona: PersonaProfile) -> None:
        self.persona = persona

    def build_system_prompt(self) -> str:
        """Combine system_prompt + tone_instruction + few_shot examples + banned_patterns."""
        parts: list[str] = []

        if self.persona.system_prompt:
            parts.append(self.persona.system_prompt)

        if self.persona.tone_instruction:
            parts.append(f"Tone: {self.persona.tone_instruction}")

        if self.persona.few_shot_examples:
            parts.append("Examples:")
            for i, example in enumerate(self.persona.few_shot_examples, 1):
                inp = example.get("input", "")
                out = example.get("output", "")
                parts.append(f"  Example {i}:")
                parts.append(f"    Input: {inp}")
                parts.append(f"    Output: {out}")

        if self.persona.banned_patterns:
            parts.append("Banned patterns (do NOT use these):")
            for pattern in self.persona.banned_patterns:
                parts.append(f"  - {pattern}")

        return "\n".join(parts)

    def check_style_consistency(self, content: str) -> dict[str, Any]:
        """Check content for banned patterns and language consistency.

        Returns a dict with:
          - score: float (0.0-1.0)
          - issues: list[str]
          - threshold: float
        """
        issues: list[str] = []
        threshold = self.persona.style_consistency_threshold

        if not content:
            return {"score": 1.0, "issues": [], "threshold": threshold}

        # Check banned patterns
        for pattern in self.persona.banned_patterns:
            if pattern.lower() in content.lower():
                issues.append(f"Banned pattern found: '{pattern}'")

        # Calculate score
        if issues:
            # Each issue reduces score proportionally, minimum 0.0
            penalty = min(len(issues) * 0.25, 1.0)
            score = max(0.0, 1.0 - penalty)
        else:
            score = 1.0

        return {"score": score, "issues": issues, "threshold": threshold}
"""Persona Engine — style analysis, few-shot selection, consistency scoring.

Three levels of modelling:
  L1 — Basic prompt injection (system_prompt + tone_instruction)
  L2 — Few-shot example selection from historical content
  L3 — LoRA fine-tuning (planned, not yet implemented)
"""

from __future__ import annotations

import re
from typing import Any

from app.models.persona import Persona


class PersonaEngine:
    """Core service for persona-based style modelling & consistency checks."""

    def __init__(self, persona: Persona) -> None:
        self.persona = persona

    # ── Prompt assembly ──────────────────────────────────────────────

    def build_system_prompt(self) -> str:
        """Assemble the final system prompt from persona config + few-shot examples."""
        parts: list[str] = []

        if self.persona.system_prompt:
            parts.append(self.persona.system_prompt)
        if self.persona.tone_instruction:
            parts.append(f"\nTone: {self.persona.tone_instruction}")

        # Inject few-shot examples (L2)
        examples = self.persona.few_shot_examples or []
        if examples:
            parts.append("\n\nReference style examples:")
            for i, ex in enumerate(examples[:3], 1):
                text = ex.get("content", "")[:300]
                parts.append(f"\n--- Example {i} ---\n{text}")

        if self.persona.banned_patterns:
            patterns = ", ".join(self.persona.banned_patterns)
            parts.append(f"\n\nAvoid: {patterns}")

        return "\n".join(parts)

    def build_generation_prompt(self, topic: dict[str, Any]) -> list[dict[str, str]]:
        """Build the LangChain-compatible message list for content generation."""
        system = self.build_system_prompt()

        user = (
            f"Topic: {topic.get('title', '')}\n\n"
            f"Summary: {topic.get('summary', '')}\n\n"
            f"Source: {topic.get('source', '')}\n"
            f"URL: {topic.get('url', '')}\n\n"
        )

        if self.persona.language == "zh":
            user += (
                "请根据以上主题，用中文撰写一篇小红书风格的图文笔记。\n"
                "要求：\n"
                "- 标题吸引眼球，带emoji\n"
                "- 正文有个人观点和情绪表达\n"
                "- 结尾带互动引导\n"
                "- 2-5个相关标签\n"
                "- 约200-500字"
            )
        else:
            user += (
                "Write a concise social media post based on this topic.\n"
                "Requirements:\n"
                "- Engaging opening\n"
                "- 1-2 relevant hashtags\n"
                "- Max 280 characters"
            )

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

    # ── Style consistency ────────────────────────────────────────────

    def check_style_consistency(self, content: str) -> dict[str, Any]:
        """Rule-based style consistency heuristics (L1/L2).

        In production this would use embedding cosine similarity against
        the persona's style_vector.  Here we apply fast heuristics.
        """
        issues: list[str] = []
        score = 1.0

        # Check banned patterns
        for pattern in self.persona.banned_patterns or []:
            if re.search(re.escape(pattern), content, re.IGNORECASE):
                issues.append(f"Contains banned pattern: '{pattern}'")
                score -= 0.15

        # Language check
        lang = self.persona.language
        if lang == "zh":
            zh_chars = len(re.findall(r"[一-鿿]", content))
            if zh_chars < 10:
                issues.append("Insufficient Chinese characters for zh persona")
                score -= 0.2
        elif lang == "en":
            en_words = len(content.split())
            if en_words < 5:
                issues.append("Too few English words for en persona")
                score -= 0.2

        return {"score": max(0.0, score), "issues": issues, "threshold": self.persona.style_consistency_threshold}
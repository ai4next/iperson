from __future__ import annotations

from typing import Any

from iperson.core.persona.profile import PersonaProfile


class PersonaEngine:
    """Wraps a persona and provides the system prompt from its soul."""

    def __init__(self, persona: PersonaProfile) -> None:
        self.persona = persona

    def build_system_prompt(self) -> str:
        """Return the soul.md content as the system prompt."""
        return self.persona.soul_content

    def check_style_consistency(self, content: str) -> dict[str, Any]:
        """Stub — always returns pass. Reserved for future soul-based checks."""
        return {"score": 1.0, "issues": [], "threshold": 0.7}
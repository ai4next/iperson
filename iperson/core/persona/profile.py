from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import yaml


class PersonaProfile:
    """Defines the creator's "voice" that gets injected into content generation pipelines."""

    def __init__(self, **kwargs: Any) -> None:
        self.id: str = kwargs.get("id", str(uuid.uuid4()))
        self.name: str = kwargs.get("name", "default")
        self.language: str = kwargs.get("language", "zh")
        self.system_prompt: str = kwargs.get("system_prompt", "")
        self.tone_instruction: str = kwargs.get("tone_instruction", "")
        self.style_profile: dict[str, Any] = kwargs.get("style_profile", {})
        self.few_shot_examples: list[dict[str, Any]] = kwargs.get("few_shot_examples", [])
        self.banned_patterns: list[str] = kwargs.get("banned_patterns", [])
        self.keywords: list[str] = kwargs.get("keywords", [])
        self.focus_areas: list[str] = kwargs.get("focus_areas", [])
        self.content_types: list[str] = kwargs.get("content_types", [])

    @property
    def style_consistency_threshold(self) -> float:
        return 0.7

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "language": self.language,
            "system_prompt": self.system_prompt,
            "tone_instruction": self.tone_instruction,
            "style_profile": self.style_profile,
            "few_shot_examples": self.few_shot_examples,
            "banned_patterns": self.banned_patterns,
            "keywords": self.keywords,
            "focus_areas": self.focus_areas,
            "content_types": self.content_types,
        }


def load_persona_from_yaml(yaml_str: str) -> PersonaProfile:
    """Load a PersonaProfile from a YAML string."""
    data = yaml.safe_load(yaml_str)
    if data is None:
        data = {}
    return PersonaProfile(**data)


def load_persona_from_file(path: str | Path) -> PersonaProfile:
    """Load a PersonaProfile from a YAML file."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        data = {}
    return PersonaProfile(**data)


def save_persona_to_file(persona: PersonaProfile, path: str | Path) -> None:
    """Save a PersonaProfile to a YAML file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(persona.to_dict(), f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def create_default_persona(name: str = "default") -> PersonaProfile:
    """Create a PersonaProfile with sensible defaults."""
    return PersonaProfile(
        id=str(uuid.uuid4()),
        name=name,
        language="zh",
        system_prompt="",
        tone_instruction="",
        style_profile={},
        few_shot_examples=[],
        banned_patterns=[
            "值得注意的是",
            "总的来说",
            "综上所述",
            "在...方面",
        ],
        keywords=[],
        focus_areas=[],
        content_types=[],
    )
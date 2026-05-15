from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import yaml

PERSONAS_DIR = Path("~/.iperson/personas").expanduser()

DEFAULT_CONFIG: dict[str, Any] = {
    "is_active": True,
}


class PersonaProfile:
    """Defines the creator's voice via soul.md + config.yaml."""

    def __init__(self, **kwargs: Any) -> None:
        self.id: str = kwargs.get("id", str(uuid.uuid4()))
        self.name: str = kwargs.get("name", "default")
        self.soul_content: str = kwargs.get("soul_content", "")
        self.config: dict[str, Any] = kwargs.get("config", dict(DEFAULT_CONFIG))


def _config_path(name: str) -> Path:
    return PERSONAS_DIR / name / "config.yaml"


def _soul_path(name: str) -> Path:
    return PERSONAS_DIR / name / "soul.md"


def load_persona(name: str) -> PersonaProfile | None:
    """Load a persona from ``{PERSONAS_DIR}/{name}/``.

    Returns None if the directory or soul.md does not exist.
    """
    soul_path = _soul_path(name)
    if not soul_path.exists():
        return None
    soul_content = soul_path.read_text(encoding="utf-8")

    cfg = dict(DEFAULT_CONFIG)
    config_path = _config_path(name)
    if config_path.exists():
        with open(config_path) as f:
            cfg.update(yaml.safe_load(f) or {})

    return PersonaProfile(name=name, soul_content=soul_content, config=cfg)


def save_persona(persona: PersonaProfile) -> Path:
    """Write ``soul.md`` and ``config.yaml`` into ``{PERSONAS_DIR}/{persona.name}/``."""
    persona_dir = PERSONAS_DIR / persona.name
    persona_dir.mkdir(parents=True, exist_ok=True)

    soul_path = persona_dir / "soul.md"
    soul_path.write_text(persona.soul_content, encoding="utf-8")

    config_path = persona_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(persona.config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return soul_path


def create_default_persona(name: str = "default") -> PersonaProfile:
    """Create a PersonaProfile with a default soul template."""
    soul = f"""# {name} 的人设灵魂

## 基本定位
{name} 是一个内容创作者。

## 语气风格
- 专业但不枯燥
- 有自己的观点和态度
- 善用比喻和故事

## 写作规范
- 开头直接切入主题，不要铺垫
- 多用短句，段落不超过 5 行
- 避免 AI 套话
"""
    return PersonaProfile(name=name, soul_content=soul, config=dict(DEFAULT_CONFIG))


def list_personas() -> list[str]:
    """List all available persona names by scanning subdirectories."""
    if not PERSONAS_DIR.exists():
        return []
    return sorted(
        d.name for d in PERSONAS_DIR.iterdir() if d.is_dir() and (d / "soul.md").exists()
    )
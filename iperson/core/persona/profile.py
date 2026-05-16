from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import yaml

PERSONAS_DIR = Path("~/.iperson/personas").expanduser()
GLOBAL_CONFIG_PATH = PERSONAS_DIR / "config.yaml"

DEFAULT_CONFIG: dict[str, Any] = {
    "is_active": True,
    "pipeline": {
        "topic_selection": True,
        "nodes": [
            {
                "id": "research",
                "agent": {
                    "prompt": "~/.iperson/prompts/research.md",
                    "model": "openai:gpt-4o",
                    "skills": [],
                },
            },
            {
                "id": "generate",
                "agent": {
                    "prompt": "~/.iperson/prompts/generate.md",
                    "model": "anthropic:claude-sonnet-4-6",
                    "skills": [],
                },
                "hooks": {
                    "after": [
                        {"hook": "quality.humanizer", "config": {"min_score": 0.35, "max_iterations": 2}}
                    ],
                },
            },
            {
                "id": "publish",
                "agent": {
                    "prompt": "~/.iperson/prompts/publish.md",
                    "model": "openai:gpt-4o",
                    "skills": [],
                },
                "config": {"platforms": ["xiaohongshu", "wechat", "zhihu"]},
            },
        ],
    },
}


def load_global_config() -> dict[str, Any]:
    """Load the global persona config from ``{PERSONAS_DIR}/config.yaml``.

    Returns DEFAULT_CONFIG if the file does not exist.
    """
    if not GLOBAL_CONFIG_PATH.exists():
        return dict(DEFAULT_CONFIG)
    with open(GLOBAL_CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}


def _migrate_pipeline_config(cfg: dict[str, Any]) -> bool:
    """Migrate old pipeline config format to current.

    Returns True if the config was modified (caller should persist to disk).
    """
    pipeline = cfg.get("pipeline")
    if not isinstance(pipeline, dict):
        return False

    nodes = pipeline.get("nodes", [])
    old_topic_nodes = [n for n in nodes if n.get("node") == "builtin.topic_selection"]
    if not old_topic_nodes:
        return False

    # Remove old builtin.topic_selection nodes
    pipeline["nodes"] = [n for n in nodes if n.get("node") != "builtin.topic_selection"]

    # Set topic_selection flag if not already present
    if "topic_selection" not in pipeline:
        pipeline["topic_selection"] = True

    return True


def ensure_global_config() -> dict[str, Any]:
    """Load or create the global persona config.

    If ``{PERSONAS_DIR}/config.yaml`` does not exist, writes DEFAULT_CONFIG
    to disk first, so the user can see and edit it.
    """
    if GLOBAL_CONFIG_PATH.exists():
        with open(GLOBAL_CONFIG_PATH) as f:
            cfg = yaml.safe_load(f) or {}
        if _migrate_pipeline_config(cfg):
            with open(GLOBAL_CONFIG_PATH, "w") as f:
                yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return cfg

    GLOBAL_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    cfg = dict(DEFAULT_CONFIG)
    with open(GLOBAL_CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return cfg


class PersonaProfile:
    """Defines the creator's voice via soul.md + config.yaml."""

    def __init__(self, **kwargs: Any) -> None:
        self.id: str = kwargs.get("id", str(uuid.uuid4()))
        self.name: str = kwargs.get("name", "default")
        self.soul_content: str = kwargs.get("soul_content", "")
        self.config: dict[str, Any] = kwargs.get("config", dict(DEFAULT_CONFIG))
        self.pipeline: dict[str, Any] = kwargs.get("pipeline", self.config.pop("pipeline", {}))


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

    cfg = ensure_global_config()
    config_path = _config_path(name)
    if config_path.exists():
        with open(config_path) as f:
            raw = yaml.safe_load(f) or {}
        if _migrate_pipeline_config(raw):
            with open(config_path, "w") as f:
                yaml.dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        cfg.update(raw)

    pipeline = cfg.pop("pipeline", {})

    return PersonaProfile(name=name, soul_content=soul_content, config=cfg, pipeline=pipeline)


def save_persona(persona: PersonaProfile) -> Path:
    """Write ``soul.md`` and ``config.yaml`` into ``{PERSONAS_DIR}/{persona.name}/``."""
    persona_dir = PERSONAS_DIR / persona.name
    persona_dir.mkdir(parents=True, exist_ok=True)

    soul_path = persona_dir / "soul.md"
    soul_path.write_text(persona.soul_content, encoding="utf-8")

    config_path = persona_dir / "config.yaml"
    output = dict(persona.config)
    output["pipeline"] = persona.pipeline
    with open(config_path, "w") as f:
        yaml.dump(output, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return soul_path


def create_default_persona(name: str = "default") -> PersonaProfile:
    """Create a PersonaProfile with a default soul template.

    Uses the global ``{PERSONAS_DIR}/config.yaml`` as the base config if it exists,
    otherwise falls back to the built-in DEFAULT_CONFIG.
    """
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
    cfg = ensure_global_config()
    pipeline = cfg.pop("pipeline", {})
    return PersonaProfile(name=name, soul_content=soul, config=cfg, pipeline=pipeline)


def list_personas() -> list[str]:
    """List all available persona names by scanning subdirectories."""
    if not PERSONAS_DIR.exists():
        return []
    return sorted(
        d.name for d in PERSONAS_DIR.iterdir() if d.is_dir() and (d / "soul.md").exists()
    )
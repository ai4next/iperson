from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

DEFAULT_CONFIG: dict[str, Any] = {
    "data_dir": "~/.iperson/data",
    "output_dir": "~/.iperson/output",
    "llm": {
        "provider": "openai",
        "api_key": "",
        "model": "gpt-4o",
    },
    "providers": [
        {"stage": "default", "provider": "openai", "model": "gpt-4o", "temperature": 0.7},
        {"stage": "generation", "provider": "openai", "model": "gpt-4o", "temperature": 0.8},
        {"stage": "audit", "provider": "openai", "model": "gpt-4o", "temperature": 0.3},
        {"stage": "humanizer", "provider": "openai", "model": "gpt-4o", "temperature": 0.5},
    ],
    "db": {
        "path": "~/.iperson/data/iperson.db",
    },
}

_CONFIG_DIR = Path("~/.iperson").expanduser()
_CONFIG_PATH = _CONFIG_DIR / "config.yaml"


def _env_override(key: str, default: Any) -> Any:
    """Check for IPERSON_<UPPER_KEY> env var override."""
    env_key = f"IPERSON_{key.upper()}"
    return os.environ.get(env_key, default)


def load_config() -> dict[str, Any]:
    """Load configuration from ~/.iperson/config.yaml with env var overrides."""
    config = copy.deepcopy(DEFAULT_CONFIG)

    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            user_config = yaml.safe_load(f) or {}
        _deep_merge(config, user_config)

    # Env var overrides for top-level keys
    for key in list(config.keys()):
        env_val = _env_override(key, None)
        if env_val is not None:
            config[key] = env_val

    # Env var overrides for nested llm keys
    if isinstance(config.get("llm"), dict):
        for subkey in list(config["llm"].keys()):
            env_key = f"llm_{subkey}"
            env_val = _env_override(env_key, None)
            if env_val is not None:
                config["llm"][subkey] = env_val

    return config


def _deep_merge(base: dict, override: dict) -> None:
    """Recursively merge override dict into base dict."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def get_data_dir() -> Path:
    """Get the data directory path."""
    config = load_config()
    return Path(config["data_dir"]).expanduser()


def get_output_dir() -> Path:
    """Get the output directory path."""
    config = load_config()
    return Path(config["output_dir"]).expanduser()


def ensure_data_dirs() -> None:
    """Create data and output directories if they don't exist."""
    get_data_dir().mkdir(parents=True, exist_ok=True)
    get_output_dir().mkdir(parents=True, exist_ok=True)


class StageProvider(BaseModel):
    """Per-stage LLM provider configuration."""

    stage: str = "default"
    provider: str = "openai"
    model: str = "gpt-4o"
    temperature: float = 0.7
    api_key: str | None = None
    base_url: str | None = None
    max_retries: int = 3
    timeout: int = 60
    max_tokens: int | None = None


def _merge_llm_api_key(provider: dict, llm_cfg: dict) -> dict:
    """Merge top-level llm api_key into per-stage provider config as fallback."""
    return {**provider, "api_key": provider.get("api_key") or llm_cfg.get("api_key", "")}


def get_provider_for_stage(stage: str) -> StageProvider:
    """Find the matching provider config for a pipeline stage, falling back to 'default'."""
    config = load_config()
    providers = config.get("providers", [])
    if not isinstance(providers, list):
        providers = []
    llm_cfg = config.get("llm", {})
    if not isinstance(llm_cfg, dict):
        llm_cfg = {}

    for p in providers:
        if isinstance(p, dict) and p.get("stage") == stage:
            return StageProvider(**_merge_llm_api_key(p, llm_cfg))

    for p in providers:
        if isinstance(p, dict) and p.get("stage") == "default":
            return StageProvider(**_merge_llm_api_key(p, llm_cfg))

    return StageProvider(
        provider=llm_cfg.get("provider", "openai"),
        model=llm_cfg.get("model", "gpt-4o"),
        api_key=llm_cfg.get("api_key", ""),
    )

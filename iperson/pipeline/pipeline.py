from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from iperson.config import get_data_dir


class PipelineValidationError(Exception):
    """Raised when a pipeline configuration is invalid."""


_REQUIRED_PIPELINE_FIELDS = ["name", "stages"]


def validate_pipeline(data: dict) -> list[str]:
    """Validate a pipeline data structure. Returns list of error messages."""
    errors: list[str] = []
    for field in _REQUIRED_PIPELINE_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")

    stages = data.get("stages", [])
    if not isinstance(stages, list):
        errors.append("'stages' must be a list")
    elif not stages:
        errors.append("'stages' list is empty")
    else:
        for i, stage in enumerate(stages):
            if not isinstance(stage, dict):
                errors.append(f"Stage {i} must be a dict")
            elif "plugin" not in stage:
                errors.append(f"Stage {i} missing required 'plugin' field")

    # Validate topic_selection field
    ts = data.get("topic_selection")
    if ts is not None and not isinstance(ts, bool):
        errors.append("'topic_selection' must be a boolean")

    return errors


def load_pipeline_from_yaml(yaml_str: str) -> dict[str, Any]:
    """Parse a YAML string into a pipeline dictionary.

    Returns a dict with keys: name, description, topic_selection, stages.
    Each stage has: plugin (str), config (dict, default empty).
    """
    data: dict[str, Any] = yaml.safe_load(yaml_str)
    if not isinstance(data, dict):
        raise ValueError("Pipeline YAML must be a mapping")
    if "name" not in data:
        raise ValueError("Pipeline must have a 'name' field")
    if "stages" not in data:
        data["stages"] = []
    if "topic_selection" not in data:
        data["topic_selection"] = False

    # Normalize stages: ensure each has a config dict
    normalized_stages: list[dict[str, Any]] = []
    for stage in data["stages"]:
        if not isinstance(stage, dict):
            raise ValueError("Each stage must be a mapping")
        if "plugin" not in stage:
            raise ValueError("Each stage must have a 'plugin' field")
        if "config" not in stage or stage["config"] is None:
            stage["config"] = {}
        normalized_stages.append(stage)

    data["stages"] = normalized_stages
    return data


def load_pipeline_from_file(path: str) -> dict[str, Any]:
    """Load a pipeline from a YAML file path."""
    file_path = Path(path).expanduser()
    if not file_path.exists():
        raise FileNotFoundError(f"Pipeline file not found: {file_path}")
    return load_pipeline_from_yaml(file_path.read_text(encoding="utf-8"))


def load_pipeline(name: str) -> dict[str, Any]:
    """Load a built-in pipeline by name from data_dir/pipelines/{name}.yaml."""
    data_dir = get_data_dir()
    pipeline_path = data_dir / "pipelines" / f"{name}.yaml"
    if not pipeline_path.exists():
        raise FileNotFoundError(
            f"Pipeline '{name}' not found at {pipeline_path}. "
            f"Available pipelines: {', '.join(list_pipelines())}"
        )
    data = load_pipeline_from_file(str(pipeline_path))
    errors = validate_pipeline(data)
    if errors:
        raise PipelineValidationError(
            f"Pipeline '{name}' is invalid: {'; '.join(errors)}"
        )
    return data


def list_pipelines() -> list[str]:
    """List available built-in pipeline names."""
    data_dir = get_data_dir()
    pipelines_dir = data_dir / "pipelines"
    if not pipelines_dir.exists():
        return []
    return sorted(
        p.stem for p in pipelines_dir.glob("*.yaml") if p.is_file()
    )
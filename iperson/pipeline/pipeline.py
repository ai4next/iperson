from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from iperson.config import get_data_dir


class PipelineValidationError(Exception):
    """Raised when a pipeline configuration is invalid."""


_REQUIRED_PIPELINE_FIELDS = ["name", "nodes"]


def validate_pipeline(data: dict) -> list[str]:
    """Validate a pipeline data structure. Returns list of error messages."""
    errors: list[str] = []
    for field in _REQUIRED_PIPELINE_FIELDS:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")

    nodes = data.get("nodes", [])
    if not isinstance(nodes, list):
        errors.append("'nodes' must be a list")
    elif not nodes:
        errors.append("'nodes' list is empty")
    else:
        for i, node in enumerate(nodes):
            if not isinstance(node, dict):
                errors.append(f"Node {i} must be a dict")
            elif "node" not in node:
                errors.append(f"Node {i} missing required 'node' field")

    return errors


def load_pipeline_from_yaml(yaml_str: str) -> dict[str, Any]:
    """Parse a YAML string into a pipeline dictionary.

    Returns a dict with keys: name, description, nodes.
    Each node has: node (str), config (dict, default empty).
    """
    data: dict[str, Any] = yaml.safe_load(yaml_str)
    if not isinstance(data, dict):
        raise ValueError("Pipeline YAML must be a mapping")
    if "name" not in data:
        raise ValueError("Pipeline must have a 'name' field")
    if "nodes" not in data:
        data["nodes"] = []

    normalized_nodes: list[dict[str, Any]] = []
    for node in data["nodes"]:
        if not isinstance(node, dict):
            raise ValueError("Each node must be a mapping")
        if "node" not in node:
            raise ValueError("Each node must have a 'node' field")
        if "config" not in node or node["config"] is None:
            node["config"] = {}
        normalized_nodes.append(node)

    data["nodes"] = normalized_nodes
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
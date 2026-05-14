from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from iperson.config import get_data_dir


def load_recipe_from_yaml(yaml_str: str) -> dict[str, Any]:
    """Parse a YAML string into a recipe dictionary.

    Returns a dict with keys: name, description, stages.
    Each stage has: plugin (str), config (dict, default empty).
    """
    data: dict[str, Any] = yaml.safe_load(yaml_str)
    if not isinstance(data, dict):
        raise ValueError("Recipe YAML must be a mapping")
    if "name" not in data:
        raise ValueError("Recipe must have a 'name' field")
    if "stages" not in data:
        data["stages"] = []

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


def load_recipe_from_file(path: str) -> dict[str, Any]:
    """Load a recipe from a YAML file path."""
    file_path = Path(path).expanduser()
    if not file_path.exists():
        raise FileNotFoundError(f"Recipe file not found: {file_path}")
    return load_recipe_from_yaml(file_path.read_text(encoding="utf-8"))


def load_recipe(name: str) -> dict[str, Any]:
    """Load a built-in recipe by name from data_dir/recipes/{name}.yaml."""
    data_dir = get_data_dir()
    recipe_path = data_dir / "recipes" / f"{name}.yaml"
    if not recipe_path.exists():
        raise FileNotFoundError(
            f"Recipe '{name}' not found at {recipe_path}. "
            f"Available recipes: {', '.join(list_recipes())}"
        )
    return load_recipe_from_file(str(recipe_path))


def list_recipes() -> list[str]:
    """List available built-in recipe names."""
    data_dir = get_data_dir()
    recipes_dir = data_dir / "recipes"
    if not recipes_dir.exists():
        return []
    return sorted(
        p.stem for p in recipes_dir.glob("*.yaml") if p.is_file()
    )
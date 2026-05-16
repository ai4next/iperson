"""Tests for AgentNodeFactory."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def prompts_dir(tmp_path: Path) -> Path:
    d = tmp_path / "prompts"
    d.mkdir()
    (d / "test.md").write_text("You are a test agent.", encoding="utf-8")
    return d


def test_load_prompt_from_file(prompts_dir: Path) -> None:
    """AgentNodeFactory should load system prompt from a file."""
    from iperson.pipeline.agent_factory import load_prompt

    prompt = load_prompt(str(prompts_dir / "test.md"))
    assert prompt == "You are a test agent."


def test_load_prompt_missing_file() -> None:
    from iperson.pipeline.agent_factory import load_prompt

    with pytest.raises(FileNotFoundError):
        load_prompt("~/.iperson/prompts/nonexistent.md")


def test_parse_skill_sources_bare_paths() -> None:
    """Bare strings should be converted to (path, label) tuples."""
    from iperson.pipeline.agent_factory import parse_skill_sources

    config = ["~/.iperson/skills/writing/", "~/.iperson/skills/seo/"]
    result = parse_skill_sources(config)

    assert len(result) == 2
    assert all(isinstance(s, tuple) and len(s) == 2 for s in result)


def test_parse_skill_sources_with_labels() -> None:
    from iperson.pipeline.agent_factory import parse_skill_sources

    config = [
        {"source": "~/.iperson/skills/writing/", "label": "Writing Skills"},
        {"source": "~/.iperson/skills/seo/", "label": "SEO"},
    ]
    result = parse_skill_sources(config)

    assert ("~/.iperson/skills/writing/", "Writing Skills") in result
    assert ("~/.iperson/skills/seo/", "SEO") in result
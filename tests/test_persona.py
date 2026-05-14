from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import yaml

from iperson.core.persona.profile import (
    PersonaProfile,
    create_default_persona,
    load_persona_from_file,
    load_persona_from_yaml,
    save_persona_to_file,
)
from iperson.core.persona.engine import PersonaEngine

SAMPLE_YAML = """
name: "科技博主小明"
language: zh
system_prompt: "你是一个科技博主。"
tone_instruction: "专业但不枯燥"
keywords: ["AI", "RAG"]
banned_patterns: ["值得注意的是"]
focus_areas: ["AI", "编程"]
content_types: ["技术博客"]
"""


def test_load_from_yaml() -> None:
    """Load from YAML string, verify all fields."""
    persona = load_persona_from_yaml(SAMPLE_YAML)
    assert persona.name == "科技博主小明"
    assert persona.language == "zh"
    assert persona.system_prompt == "你是一个科技博主。"
    assert persona.tone_instruction == "专业但不枯燥"
    assert persona.keywords == ["AI", "RAG"]
    assert persona.banned_patterns == ["值得注意的是"]
    assert persona.focus_areas == ["AI", "编程"]
    assert persona.content_types == ["技术博客"]
    assert persona.style_profile == {}
    assert persona.few_shot_examples == []


def test_load_from_yaml_missing_fields() -> None:
    """Missing optional fields get defaults."""
    minimal_yaml = """
name: "minimal"
language: en
system_prompt: "test"
"""
    persona = load_persona_from_yaml(minimal_yaml)
    assert persona.name == "minimal"
    assert persona.language == "en"
    assert persona.system_prompt == "test"
    assert persona.tone_instruction == ""
    assert persona.keywords == []
    assert persona.banned_patterns == []
    assert persona.focus_areas == []
    assert persona.content_types == []
    assert persona.style_profile == {}
    assert persona.few_shot_examples == []


def test_create_default() -> None:
    """Default persona has correct name and banned_patterns."""
    persona = create_default_persona()
    assert persona.name == "default"
    assert persona.banned_patterns == [
        "值得注意的是",
        "总的来说",
        "综上所述",
        "在...方面",
    ]
    assert persona.language == "zh"
    assert persona.system_prompt == ""
    assert persona.tone_instruction == ""
    assert persona.keywords == []
    assert persona.focus_areas == []
    assert persona.content_types == []
    assert persona.style_profile == {}
    assert persona.few_shot_examples == []

    # Verify id is a valid UUID
    uuid.UUID(persona.id)


def test_create_default_custom_name() -> None:
    """Default persona with custom name."""
    persona = create_default_persona(name="tech-blogger")
    assert persona.name == "tech-blogger"
    assert persona.banned_patterns == [
        "值得注意的是",
        "总的来说",
        "综上所述",
        "在...方面",
    ]


def test_save_and_load(tmp_path: Path) -> None:
    """Save to file, load back, verify fields match."""
    persona = create_default_persona(name="test-persona")
    persona.language = "en"
    persona.system_prompt = "You are a tech blogger."
    persona.tone_instruction = "Professional but approachable"
    persona.keywords = ["python", "AI"]
    persona.banned_patterns = ["importantly", "notably"]
    persona.focus_areas = ["backend", "ML"]
    persona.content_types = ["blog"]
    persona.style_profile = {"formality": "high"}
    persona.few_shot_examples = [
        {"input": "hello", "output": "world"},
    ]

    filepath = tmp_path / "persona.yaml"
    save_persona_to_file(persona, filepath)

    assert filepath.exists()

    loaded = load_persona_from_file(filepath)
    assert loaded.id == persona.id
    assert loaded.name == persona.name
    assert loaded.language == persona.language
    assert loaded.system_prompt == persona.system_prompt
    assert loaded.tone_instruction == persona.tone_instruction
    assert loaded.keywords == persona.keywords
    assert loaded.banned_patterns == persona.banned_patterns
    assert loaded.focus_areas == persona.focus_areas
    assert loaded.content_types == persona.content_types
    assert loaded.style_profile == persona.style_profile
    assert loaded.few_shot_examples == persona.few_shot_examples


def test_to_dict_roundtrip() -> None:
    """to_dict() contains all expected keys."""
    persona = create_default_persona(name="dict-test")
    persona.language = "en"
    persona.system_prompt = "test prompt"
    persona.tone_instruction = "test tone"
    persona.keywords = ["a", "b"]
    persona.banned_patterns = ["bad"]
    persona.focus_areas = ["x"]
    persona.content_types = ["y"]
    persona.style_profile = {"key": "val"}
    persona.few_shot_examples = [{"in": "out"}]

    d = persona.to_dict()
    assert d["id"] == persona.id
    assert d["name"] == "dict-test"
    assert d["language"] == "en"
    assert d["system_prompt"] == "test prompt"
    assert d["tone_instruction"] == "test tone"
    assert d["keywords"] == ["a", "b"]
    assert d["banned_patterns"] == ["bad"]
    assert d["focus_areas"] == ["x"]
    assert d["content_types"] == ["y"]
    assert d["style_profile"] == {"key": "val"}
    assert d["few_shot_examples"] == [{"in": "out"}]


def test_style_consistency_threshold() -> None:
    """style_consistency_threshold returns 0.7."""
    persona = create_default_persona()
    assert persona.style_consistency_threshold == 0.7


def test_build_system_prompt() -> None:
    """System prompt includes persona content."""
    persona = create_default_persona(name="test")
    persona.system_prompt = "You are a helpful assistant."
    persona.tone_instruction = "Be concise."
    persona.banned_patterns = ["bad word"]

    engine = PersonaEngine(persona)
    prompt = engine.build_system_prompt()

    assert "You are a helpful assistant." in prompt
    assert "Be concise." in prompt
    assert "bad word" in prompt
    assert "banned" in prompt.lower()


def test_build_system_prompt_with_examples() -> None:
    """Few-shot examples appear in prompt."""
    persona = create_default_persona(name="test")
    persona.system_prompt = "You are a writer."
    persona.few_shot_examples = [
        {"input": "Hello", "output": "Hi there!"},
        {"input": "How are you?", "output": "I'm great!"},
    ]

    engine = PersonaEngine(persona)
    prompt = engine.build_system_prompt()

    assert "You are a writer." in prompt
    assert "Hello" in prompt
    assert "Hi there!" in prompt
    assert "How are you?" in prompt
    assert "I'm great!" in prompt


def test_check_style_consistency_pass() -> None:
    """Clean content returns score 1.0."""
    persona = create_default_persona(name="test")
    persona.banned_patterns = ["bad word", "terrible phrase"]
    persona.language = "zh"

    engine = PersonaEngine(persona)
    result = engine.check_style_consistency("这是一篇干净的内容，没有任何问题。")

    assert result["score"] == 1.0
    assert result["issues"] == []
    assert result["threshold"] == 0.7


def test_check_style_consistency_banned_pattern() -> None:
    """Content with banned pattern scores < 1.0."""
    persona = create_default_persona(name="test")
    persona.banned_patterns = ["值得注意的是"]
    persona.language = "zh"

    engine = PersonaEngine(persona)
    result = engine.check_style_consistency(
        "值得注意的是，这个内容包含了违禁模式。"
    )

    assert result["score"] < 1.0
    assert len(result["issues"]) > 0
    assert any("值得注意的是" in issue for issue in result["issues"])
    assert result["threshold"] == 0.7


def test_check_style_consistency_english() -> None:
    """English persona, content check works."""
    persona = create_default_persona(name="test")
    persona.banned_patterns = ["importantly", "notably"]
    persona.language = "en"

    engine = PersonaEngine(persona)
    result = engine.check_style_consistency(
        "This is clean English content with no banned patterns."
    )

    assert result["score"] == 1.0
    assert result["issues"] == []

    # Now test with banned pattern
    result2 = engine.check_style_consistency(
        "Importantly, this contains a banned pattern."
    )
    assert result2["score"] < 1.0
    assert len(result2["issues"]) > 0


def test_check_style_consistency_empty() -> None:
    """Empty content returns score 1.0 with no issues."""
    persona = create_default_persona(name="test")
    persona.banned_patterns = ["bad"]
    persona.language = "zh"

    engine = PersonaEngine(persona)
    result = engine.check_style_consistency("")

    assert result["score"] == 1.0
    assert result["issues"] == []
    assert result["threshold"] == 0.7
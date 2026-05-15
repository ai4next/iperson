from __future__ import annotations

from pathlib import Path

from iperson.core.persona.engine import PersonaEngine
from iperson.core.persona.profile import (
    PERSONAS_DIR,
    PersonaProfile,
    create_default_persona,
    list_personas,
    load_persona,
    save_persona,
)


def test_create_default() -> None:
    """Default persona has correct name and soul content."""
    persona = create_default_persona("test-blogger")
    assert persona.name == "test-blogger"
    assert "# test-blogger 的人设灵魂" in persona.soul_content
    assert "语气风格" in persona.soul_content


def test_save_and_load(tmp_path: Path, monkeypatch) -> None:
    """Save to soul.md + config.yaml, load back, verify content matches."""
    monkeypatch.setattr("iperson.core.persona.profile.PERSONAS_DIR", tmp_path)

    persona = create_default_persona("test-persona")
    persona.soul_content = "You are a tech blogger. Be concise and witty."
    persona.config = {"is_active": True, "platform": "xiaohongshu"}

    path = save_persona(persona)
    assert path.exists()
    assert path.name == "soul.md"
    assert path.parent.name == "test-persona"
    assert (tmp_path / "test-persona" / "config.yaml").exists()

    loaded = load_persona("test-persona")
    assert loaded is not None
    assert loaded.name == "test-persona"
    assert loaded.soul_content == "You are a tech blogger. Be concise and witty."
    assert loaded.config.get("is_active") is True
    assert loaded.config.get("platform") == "xiaohongshu"


def test_load_nonexistent(tmp_path, monkeypatch) -> None:
    """Loading a non-existent persona returns None."""
    monkeypatch.setattr("iperson.core.persona.profile.PERSONAS_DIR", tmp_path)
    assert load_persona("nobody") is None


def test_list_personas(tmp_path, monkeypatch) -> None:
    """list_personas returns names of directories with soul.md."""
    monkeypatch.setattr("iperson.core.persona.profile.PERSONAS_DIR", tmp_path)

    # Create two personas
    for name in ["alice", "bob"]:
        p = create_default_persona(name)
        save_persona(p)

    # A directory without soul.md should be ignored
    (tmp_path / "nope").mkdir()

    names = list_personas()
    assert names == ["alice", "bob"]


def test_build_system_prompt() -> None:
    """build_system_prompt returns the soul content."""
    persona = create_default_persona("test")
    persona.soul_content = "You are a helpful assistant. Be concise."

    engine = PersonaEngine(persona)
    prompt = engine.build_system_prompt()

    assert prompt == "You are a helpful assistant. Be concise."


def test_check_style_consistency() -> None:
    """check_style_consistency always returns pass."""
    persona = create_default_persona("test")
    engine = PersonaEngine(persona)

    result = engine.check_style_consistency("任何内容都通过")
    assert result["score"] == 1.0
    assert result["issues"] == []

    result = engine.check_style_consistency("")
    assert result["score"] == 1.0
    assert result["issues"] == []
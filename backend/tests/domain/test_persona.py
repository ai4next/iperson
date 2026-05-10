"""Tests for persona engine — prompt building, style consistency."""

from app.domain.persona import PersonaEngine
from app.models.persona import Persona


class TestPersonaEngine:
    def test_build_system_prompt_with_both_fields(self, sample_persona_dict):
        persona = Persona(**sample_persona_dict)
        engine = PersonaEngine(persona)
        prompt = engine.build_system_prompt()
        assert "tech analyst" in prompt or "锐利的" in prompt

    def test_build_system_prompt_empty_system(self):
        persona = Persona(
            tenant_id="t1", name="Test",
            system_prompt=None, tone_instruction="Keep it short.",
        )
        engine = PersonaEngine(persona)
        prompt = engine.build_system_prompt()
        assert "Keep it short." in prompt

    def test_build_generation_prompt_zh(self, sample_persona_dict):
        persona = Persona(**sample_persona_dict)
        engine = PersonaEngine(persona)
        topic = {"title": "AI breakthrough", "summary": "Great progress", "source": "test", "url": "https://x.com"}
        messages = engine.build_generation_prompt(topic)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        # Chinese template should include 小红书
        assert "小红书" in messages[1]["content"]

    def test_style_consistency_banned_patterns(self, sample_persona_dict):
        sample_persona_dict["banned_patterns"] = ["clickbait", "shocking"]
        persona = Persona(**sample_persona_dict)
        engine = PersonaEngine(persona)
        result = engine.check_style_consistency("This is shocking clickbait content")
        assert result["score"] < 0.7
        assert len(result["issues"]) > 0

    def test_style_consistency_clean_content(self, sample_persona_dict):
        persona = Persona(**sample_persona_dict)
        engine = PersonaEngine(persona)
        result = engine.check_style_consistency(
            "今天我们来聊聊AI的最新进展，这真是一个令人兴奋的领域。"
        )
        assert result["score"] >= 0.7
        assert len(result["issues"]) == 0
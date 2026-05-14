from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from iperson.core.generation.engine import GenerationEngine
from iperson.core.generation.prompts import build_generation_prompt
from iperson.core.persona.profile import PersonaProfile
from iperson.utils.llm import DummyLLM


class TestBuildGenerationMessages:
    """Tests for build_generation_prompt() in prompts.py."""

    def _format(self, persona: PersonaProfile, topic: dict[str, Any], kb_context: str = "") -> list[dict[str, str]]:
        prompt = build_generation_prompt(persona, topic, kb_context, structured=False)
        title = topic.get("title", "")
        summary = topic.get("summary", "")
        messages = prompt.format_messages(title=title, summary=summary)
        role_map = {"human": "user", "ai": "assistant"}
        return [{"role": role_map.get(m.type, m.type), "content": m.content} for m in messages]

    def test_build_with_persona_and_kb(self) -> None:
        persona = PersonaProfile(name="测试", system_prompt="你是测试助手。", language="zh")
        topic = {"title": "AI的未来", "summary": "探讨人工智能的发展趋势"}
        kb_context = "来源1: AI正在快速发展\n来源2: 2025年AI市场规模达千亿"

        messages = self._format(persona, topic, kb_context)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Knowledge Base Context" in messages[0]["content"]
        assert kb_context in messages[0]["content"]
        assert "AI的未来" in messages[1]["content"]
        assert "人工智能" in messages[1]["content"]

    def test_without_kb_context(self) -> None:
        persona = PersonaProfile(name="测试", system_prompt="你是测试助手。", language="zh")
        topic = {"title": "AI的未来", "summary": "探讨人工智能的发展趋势"}

        messages = self._format(persona, topic)

        assert len(messages) == 2
        assert messages[0]["content"] == "你是测试助手。"
        assert "Knowledge Base Context" not in messages[0]["content"]

    def test_english_persona(self) -> None:
        persona = PersonaProfile(name="Test", system_prompt="You are a test assistant.", language="en")
        topic = {"title": "Future of AI", "summary": "Exploring AI trends"}

        messages = self._format(persona, topic)

        assert len(messages) == 2
        user = messages[1]["content"]
        assert "主题" not in user
        assert "请根据以上主题" not in user
        assert "Topic:" in user
        assert "Future of AI" in user
        assert "Summary:" in user

    def test_empty_topic(self) -> None:
        persona = PersonaProfile(name="测试", system_prompt="你是测试助手。", language="zh")
        topic: dict[str, Any] = {}

        messages = self._format(persona, topic)

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"


class TestGenerationEngine:
    """Tests for GenerationEngine."""

    async def test_generation_engine_with_dummy_llm(self) -> None:
        dummy = DummyLLM()
        engine = GenerationEngine(llm=dummy)
        persona = PersonaProfile(name="测试", system_prompt="你是测试助手。", language="zh")
        topic = {"title": "测试", "summary": "测试内容"}

        result = await engine.generate(persona, topic)

        assert isinstance(result, dict)
        assert "content" in result
        assert isinstance(result["content"], str)
        assert len(result["content"]) > 0
        assert "messages" in result
        assert len(result["messages"]) == 2
        assert result["topic"] == topic

    async def test_generation_engine_custom_temperature(self) -> None:
        class TempTrackingDummy(DummyLLM):
            async def _agenerate(
                self,
                messages: list[Any],
                stop: list[str] | None = None,
                run_manager: Any = None,
                **kwargs: Any,
            ) -> ChatResult:
                self._last_temperature = self.temperature
                tracked = AIMessage(content="tracked content")
                return ChatResult(generations=[ChatGeneration(message=tracked)])

        dummy = TempTrackingDummy()
        engine = GenerationEngine(llm=dummy)
        persona = PersonaProfile(name="测试", system_prompt="你是测试助手。", language="zh")
        topic = {"title": "测试", "summary": "测试内容"}

        dummy.temperature = 0.9
        await engine.generate(persona, topic, temperature=0.9)
        assert dummy.temperature == 0.9
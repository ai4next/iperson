"""Tests for built-in topic selection in PipelineOrchestrator."""
from __future__ import annotations

from typing import Any

import pytest

from iperson.core.persona.engine import PersonaEngine
from iperson.core.persona.profile import PersonaProfile
from iperson.pipeline.context import PipelineContext
from iperson.pipeline.orchestrator import PipelineOrchestrator
from iperson.pipeline.registry import PluginRegistry
from iperson.utils.llm import DummyLLM


def _make_persona(soul: str = "你是科技博主，专注AI领域。") -> PersonaEngine:
    return PersonaEngine(PersonaProfile(name="test", soul_content=soul))


class TestTopicSelection:
    @pytest.mark.asyncio
    async def test_auto_select_topic_sets_ctx_topic(self) -> None:
        """When topic_selection=true and topic is empty, topic is auto-selected."""
        registry = PluginRegistry()
        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(topic="")
        ctx.data["llm_client"] = DummyLLM(response="RAG技术入门")
        ctx.data["persona_engine"] = _make_persona()
        ctx.kb_context = "RAG（检索增强生成）是一种结合检索和生成的AI架构。"

        pipeline = {"name": "test", "topic_selection": True, "stages": []}
        result = await orchestrator.run(ctx, pipeline)

        assert result.topic == "RAG技术入门"
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_skip_topic_selection_when_topic_provided(self) -> None:
        """When topic is explicitly provided, skip auto selection."""
        registry = PluginRegistry()
        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(topic="手动输入的选题")
        ctx.data["llm_client"] = DummyLLM(response="这个不会被使用")
        ctx.data["persona_engine"] = _make_persona()
        ctx.kb_context = "some context"

        pipeline = {"name": "test", "topic_selection": True, "stages": []}
        result = await orchestrator.run(ctx, pipeline)

        assert result.topic == "手动输入的选题"

    @pytest.mark.asyncio
    async def test_skip_topic_selection_when_disabled(self) -> None:
        """When topic_selection=false, skip even if topic is empty."""
        registry = PluginRegistry()
        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(topic="")
        ctx.data["llm_client"] = DummyLLM()
        ctx.data["persona_engine"] = _make_persona()
        ctx.kb_context = "some context"

        pipeline = {"name": "test", "topic_selection": False, "stages": []}
        result = await orchestrator.run(ctx, pipeline)

        assert result.topic == ""

    @pytest.mark.asyncio
    async def test_error_on_empty_kb_context(self) -> None:
        """When KB context is empty, topic selection should error."""
        registry = PluginRegistry()
        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(topic="")
        ctx.data["llm_client"] = DummyLLM()
        ctx.data["persona_engine"] = _make_persona()
        ctx.kb_context = ""

        pipeline = {"name": "test", "topic_selection": True, "stages": []}
        result = await orchestrator.run(ctx, pipeline)

        assert "TOPIC_SELECTION_FAILED" in [e.error_code for e in result.errors]

    @pytest.mark.asyncio
    async def test_error_on_missing_persona(self) -> None:
        """When persona engine is missing, topic selection should error."""
        registry = PluginRegistry()
        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(topic="")
        ctx.data["llm_client"] = DummyLLM()
        ctx.kb_context = "some context"

        pipeline = {"name": "test", "topic_selection": True, "stages": []}
        result = await orchestrator.run(ctx, pipeline)

        assert "TOPIC_SELECTION_FAILED" in [e.error_code for e in result.errors]

    @pytest.mark.asyncio
    async def test_error_on_missing_llm(self) -> None:
        """When LLM client is missing, topic selection should error."""
        registry = PluginRegistry()
        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(topic="")
        ctx.data["persona_engine"] = _make_persona()
        ctx.kb_context = "some context"

        pipeline = {"name": "test", "topic_selection": True, "stages": []}
        result = await orchestrator.run(ctx, pipeline)

        assert "TOPIC_SELECTION_FAILED" in [e.error_code for e in result.errors]

    @pytest.mark.asyncio
    async def test_error_on_empty_llm_response(self) -> None:
        """When LLM returns empty string, topic selection should error."""
        registry = PluginRegistry()
        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(topic="")
        ctx.data["llm_client"] = DummyLLM(response="")
        ctx.data["persona_engine"] = _make_persona()
        ctx.kb_context = "some context"

        pipeline = {"name": "test", "topic_selection": True, "stages": []}
        result = await orchestrator.run(ctx, pipeline)

        assert "TOPIC_SELECTION_FAILED" in [e.error_code for e in result.errors]
"""End-to-end integration tests for the full pipeline."""

from __future__ import annotations

from typing import Any

import pytest

from iperson.pipeline.context import PipelineContext
from iperson.pipeline.orchestrator import PipelineOrchestrator
from iperson.pipeline.pipeline import load_pipeline_from_yaml
from iperson.pipeline.registry import PluginRegistry
from iperson.pipeline.plugins import register_builtin_plugins
from iperson.core.persona.engine import PersonaEngine
from iperson.core.persona.profile import PersonaProfile
from iperson.utils.llm import DummyLLM

QUICK_RECIPE = """
name: quick-test
nodes:
  - id: research
    node: research.kb_retrieve
    config:
      top_k: 3
  - id: generate
    node: generation.article
  - id: publish
    node: publish.multiplatform
    config:
      platforms: [xiaohongshu]
"""


def _make_persona(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a minimal persona dict for testing."""
    base = {
        "name": "测试",
        "soul_content": "你是测试助手。专业但不枯燥。",
    }
    if overrides:
        base.update(overrides)
    return base


class TestQuickRecipeIntegration:
    """Integration tests that run the full quick recipe pipeline."""

    @pytest.mark.asyncio
    async def test_quick_recipe_full_pipeline(self) -> None:
        """Run full quick recipe end-to-end with DummyLLM."""
        registry = PluginRegistry()
        register_builtin_plugins(registry)
        orchestrator = PipelineOrchestrator(registry)
        recipe = load_pipeline_from_yaml(QUICK_RECIPE)

        ctx = PipelineContext(persona_name="test", topic="RAG技术入门")
        ctx.data["llm_client"] = DummyLLM(
            response="Test generated article about RAG technology."
        )
        ctx.data["platform"] = "xiaohongshu"
        ctx.data["keywords"] = ["RAG"]
        ctx.data["persona"] = _make_persona()
        ctx.kb_chunks = [
            {"text": "RAG（检索增强生成）是一种结合检索和生成的AI架构。", "index": 0},
            {"text": "RAG可以显著减少大模型的幻觉问题。", "index": 1},
        ]

        result = await orchestrator.run(ctx, recipe)

        assert result.status == "completed", f"Pipeline failed: {result.errors}"
        assert result.generated_content is not None
        assert len(result.publish_results) > 0
        assert result.publish_results[0]["platform"] == "xiaohongshu"

    @pytest.mark.asyncio
    async def test_quick_recipe_empty_kb(self) -> None:
        """Pipeline works even with no KB chunks."""
        registry = PluginRegistry()
        register_builtin_plugins(registry)
        orchestrator = PipelineOrchestrator(registry)
        recipe = load_pipeline_from_yaml(QUICK_RECIPE)

        ctx = PipelineContext(persona_name="test", topic="通用话题")
        ctx.data["llm_client"] = DummyLLM(response="Some content.")
        ctx.data["platform"] = "xiaohongshu"
        ctx.data["keywords"] = ["通用"]
        ctx.data["persona"] = _make_persona()

        result = await orchestrator.run(ctx, recipe)
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_quick_pipeline_with_topic_selection(self) -> None:
        """Quick pipeline runs with topic_selection enabled and empty topic."""
        registry = PluginRegistry()
        register_builtin_plugins(registry)
        orchestrator = PipelineOrchestrator(registry)
        recipe = load_pipeline_from_yaml("""
name: topic-selection-test
topic_selection: true
nodes:
  - id: generate
    node: generation.article
""")
        ctx = PipelineContext(persona_name="test", topic="")
        ctx.data["llm_client"] = DummyLLM(response="测试生成内容")
        ctx.data["platform"] = "xiaohongshu"
        ctx.data["keywords"] = ["test"]
        ctx.data["persona"] = _make_persona()
        ctx.data["persona_engine"] = PersonaEngine(
            PersonaProfile(name="test", soul_content="你是测试助手。专业但不枯燥。")
        )
        ctx.kb_context = "AI 技术在2025年的发展趋势分析。"

        result = await orchestrator.run(ctx, recipe)

        assert result.topic != ""
        assert result.generated_content is not None
        assert result.status == "completed"
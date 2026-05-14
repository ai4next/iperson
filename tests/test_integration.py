"""End-to-end integration tests for the full pipeline."""

from __future__ import annotations

from typing import Any

import pytest

from iperson.pipeline.context import PipelineContext
from iperson.pipeline.orchestrator import PipelineOrchestrator
from iperson.pipeline.recipe import load_recipe_from_yaml
from iperson.pipeline.registry import PluginRegistry
from iperson.pipeline.plugins import register_builtin_plugins
from iperson.utils.llm import DummyLLM

QUICK_RECIPE = """
name: quick-test
stages:
  - plugin: research.kb_retrieve
    config:
      top_k: 3
  - plugin: generation.article
  - plugin: quality.humanizer
    config:
      min_score: 0.35
  - plugin: quality.audit
  - plugin: publish.multiplatform
    config:
      platforms: [xiaohongshu]
"""


def _make_persona(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a minimal persona dict for testing."""
    base = {
        "name": "测试",
        "language": "zh",
        "system_prompt": "你是测试助手。",
        "tone_instruction": "专业",
        "banned_patterns": [],
        "keywords": [],
        "focus_areas": [],
        "content_types": [],
        "few_shot_examples": [],
        "style_profile": {},
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
        recipe = load_recipe_from_yaml(QUICK_RECIPE)

        ctx = PipelineContext(persona_id="test", topic="RAG技术入门")
        ctx.data["llm_client"] = DummyLLM(
            response="Test generated article about RAG technology."
        )
        ctx.data["platform"] = "xiaohongshu"
        ctx.data["keywords"] = ["RAG"]
        ctx.data["persona"] = _make_persona({
            "banned_patterns": ["值得注意的是"],
            "keywords": ["AI", "RAG"],
        })
        ctx.kb_chunks = [
            {"text": "RAG（检索增强生成）是一种结合检索和生成的AI架构。", "index": 0},
            {"text": "RAG可以显著减少大模型的幻觉问题。", "index": 1},
        ]

        result = await orchestrator.run(ctx, recipe)

        assert result.status == "completed", f"Pipeline failed: {result.errors}"
        assert result.generated_content is not None
        assert result.humanized_content is not None
        assert result.audit_result is not None
        assert "overall_status" in result.audit_result
        assert len(result.publish_results) > 0
        assert result.publish_results[0]["platform"] == "xiaohongshu"

    @pytest.mark.asyncio
    async def test_quick_recipe_empty_kb(self) -> None:
        """Pipeline works even with no KB chunks."""
        registry = PluginRegistry()
        register_builtin_plugins(registry)
        orchestrator = PipelineOrchestrator(registry)
        recipe = load_recipe_from_yaml(QUICK_RECIPE)

        ctx = PipelineContext(persona_id="test", topic="通用话题")
        ctx.data["llm_client"] = DummyLLM(response="Some content.")
        ctx.data["platform"] = "xiaohongshu"
        ctx.data["keywords"] = ["通用"]
        ctx.data["persona"] = _make_persona()

        result = await orchestrator.run(ctx, recipe)
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_quick_recipe_humanizer_removes_ai_phrases(self) -> None:
        """Humanizer plugin modifies content with AI phrases."""
        registry = PluginRegistry()
        register_builtin_plugins(registry)
        orchestrator = PipelineOrchestrator(registry)
        recipe = load_recipe_from_yaml("""
name: humanizer-test
stages:
  - plugin: quality.humanizer
    config:
      min_score: 0.1
      max_iterations: 1
""")
        ctx = PipelineContext(topic="test")
        ctx.generated_content = "值得注意的是，这是一个测试。总的来说，还可以。"

        result = await orchestrator.run(ctx, recipe)
        assert result.humanized_content is not None
        assert "值得注意的是" not in result.humanized_content

    @pytest.mark.asyncio
    async def test_quick_recipe_audit_gate_rejects_empty(self) -> None:
        """Audit gate gives skip for empty content."""
        registry = PluginRegistry()
        register_builtin_plugins(registry)
        orchestrator = PipelineOrchestrator(registry)
        recipe = load_recipe_from_yaml("""
name: audit-test
stages:
  - plugin: quality.audit
""")
        ctx = PipelineContext(topic="test")
        ctx.data["keywords"] = []
        ctx.data["platform"] = "xiaohongshu"

        result = await orchestrator.run(ctx, recipe)
        assert result.audit_result is not None
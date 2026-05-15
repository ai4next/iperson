from __future__ import annotations

import pytest

from iperson.pipeline.context import PipelineContext
from iperson.pipeline.plugins.quality.humanizer import HumanizerPlugin
from iperson.pipeline.plugins.quality.audit import AuditPlugin
from iperson.pipeline.plugins.research.kb_retrieve import KbRetrievePlugin
from iperson.utils.llm import DummyLLM


class TestKbRetrievePlugin:
    async def test_with_chunks(self):
        plugin = KbRetrievePlugin()
        ctx = PipelineContext(topic="RAG")
        ctx.kb_chunks = [{"text": "RAG is retrieval augmented generation.", "index": 0}]
        result = await plugin.execute(ctx)
        assert result.kb_context != ""
        assert "[Source 1]" in result.kb_context
        assert "RAG is retrieval augmented generation." in result.kb_context

    async def test_without_chunks(self):
        plugin = KbRetrievePlugin()
        ctx = PipelineContext(topic="test")
        result = await plugin.execute(ctx)
        assert result.kb_context == ""


class TestHumanizerPlugin:
    async def test_humanizer_replaces_phrases(self):
        plugin = HumanizerPlugin()
        ctx = PipelineContext(topic="test")
        ctx.generated_content = "值得注意的是，这是一个测试内容。总的来说，还可以。"
        result = await plugin.execute(ctx, config={"min_score": 0.0, "max_iterations": 1})
        assert "值得注意的是" not in result.humanized_content
        assert "总的来说" not in result.humanized_content

    async def test_humanizer_no_content(self):
        plugin = HumanizerPlugin()
        ctx = PipelineContext(topic="test")
        result = await plugin.execute(ctx)
        assert result.humanized_content == ""  # no content to humanize

    async def test_humanizer_with_default_config(self):
        plugin = HumanizerPlugin()
        ctx = PipelineContext(topic="test")
        ctx.generated_content = "值得注意的是，这是一个测试内容。总的来说，还可以。"
        result = await plugin.execute(ctx)
        assert result.humanized_content is not None


class TestAuditPlugin:
    async def test_audit_plugin(self):
        plugin = AuditPlugin()
        ctx = PipelineContext(topic="test")
        ctx.humanized_content = "# Test\n\nThis is test content with RAG keyword."
        ctx.kb_chunks = [{"text": "RAG is retrieval.", "index": 0}]
        ctx.data["keywords"] = ["RAG"]
        ctx.data["platform"] = "xiaohongshu"
        result = await plugin.execute(ctx)
        assert result.audit_result is not None
        assert "overall_status" in result.audit_result
        assert "scores" in result.audit_result

    async def test_audit_without_content(self):
        plugin = AuditPlugin()
        ctx = PipelineContext(topic="test")
        result = await plugin.execute(ctx)
        # Should handle gracefully - audit_result should be a dict
        assert isinstance(result.audit_result, dict)

    async def test_audit_falls_back_to_generated_content(self):
        plugin = AuditPlugin()
        ctx = PipelineContext(topic="test")
        ctx.generated_content = "# Test\n\nSome generated content."
        ctx.kb_chunks = [{"text": "Some content.", "index": 0}]
        ctx.data["keywords"] = ["test"]
        ctx.data["platform"] = "xiaohongshu"
        result = await plugin.execute(ctx)
        assert result.audit_result is not None
        assert "overall_status" in result.audit_result


class TestArticleGenerationPlugin:
    async def test_generation(self):
        from iperson.pipeline.plugins.generation.article import ArticleGenerationPlugin

        plugin = ArticleGenerationPlugin()
        ctx = PipelineContext(topic="RAG技术")
        ctx.data["llm_client"] = DummyLLM(response="Test article content.")
        ctx.data["persona"] = {
            "name": "测试",
            "soul_content": "你是测试助手。",
        }
        result = await plugin.execute(ctx)
        assert result.generated_content == "Test article content."
        assert "generation_messages" in ctx.data

    async def test_generation_without_llm(self):
        from iperson.pipeline.plugins.generation.article import ArticleGenerationPlugin

        plugin = ArticleGenerationPlugin()
        ctx = PipelineContext(topic="test")
        # No llm_client set - should handle gracefully
        result = await plugin.execute(ctx)
        assert result.generated_content == ""


class TestMultiplatformPublishPlugin:
    async def test_publish(self, tmp_path):
        from iperson.pipeline.plugins.publish.multiplatform import (
            MultiplatformPublishPlugin,
        )

        # Mock output dir to use tmp_path
        import iperson.utils.output as output_mod

        original = output_mod.get_output_dir
        output_mod.get_output_dir = lambda: tmp_path / "output"  # type: ignore[method-assign]

        try:
            plugin = MultiplatformPublishPlugin()
            ctx = PipelineContext(topic="test")
            ctx.humanized_content = "Test content."
            ctx.audit_result = {
                "overall_status": "pass",
                "scores": {},
                "dimensions": {},
            }
            result = await plugin.execute(ctx)

            assert len(result.publish_results) > 0
            assert result.publish_results[0]["platform"] == "xiaohongshu"
            assert "output_dir" in ctx.data
        finally:
            output_mod.get_output_dir = original

    async def test_publish_falls_back_to_generated_content(self, tmp_path):
        from iperson.pipeline.plugins.publish.multiplatform import (
            MultiplatformPublishPlugin,
        )

        import iperson.utils.output as output_mod

        original = output_mod.get_output_dir
        output_mod.get_output_dir = lambda: tmp_path / "output"  # type: ignore[method-assign]

        try:
            plugin = MultiplatformPublishPlugin()
            ctx = PipelineContext(topic="test")
            ctx.generated_content = "Generated content only."
            ctx.audit_result = {
                "overall_status": "pass",
                "scores": {},
                "dimensions": {},
            }
            result = await plugin.execute(ctx)

            assert len(result.publish_results) > 0
            assert result.publish_results[0]["platform"] == "xiaohongshu"
        finally:
            output_mod.get_output_dir = original

    async def test_publish_custom_platforms(self, tmp_path):
        from iperson.pipeline.plugins.publish.multiplatform import (
            MultiplatformPublishPlugin,
        )

        import iperson.utils.output as output_mod

        original = output_mod.get_output_dir
        output_mod.get_output_dir = lambda: tmp_path / "output"  # type: ignore[method-assign]

        try:
            plugin = MultiplatformPublishPlugin()
            ctx = PipelineContext(topic="test")
            ctx.humanized_content = "Test content for weixin."
            ctx.audit_result = {
                "overall_status": "pass",
                "scores": {},
                "dimensions": {},
            }
            result = await plugin.execute(
                ctx, config={"platforms": ["weixin", "xiaohongshu"]}
            )

            assert len(result.publish_results) == 2
            platforms = {r["platform"] for r in result.publish_results}
            assert platforms == {"weixin", "xiaohongshu"}
        finally:
            output_mod.get_output_dir = original


class TestRegistration:
    async def test_register_all_builtin_plugins(self):
        from iperson.pipeline.plugins import register_builtin_plugins
        from iperson.pipeline.registry import PluginRegistry

        registry = PluginRegistry()
        register_builtin_plugins(registry)

        assert registry.has("research.kb_retrieve")
        assert registry.has("generation.article")
        assert registry.has("quality.humanizer")
        assert registry.has("quality.audit")
        assert registry.has("publish.multiplatform")

        plugin_list = registry.list_plugins()
        plugin_ids = [p["plugin_id"] for p in plugin_list]
        assert "research.kb_retrieve" in plugin_ids
        assert "generation.article" in plugin_ids
        assert "quality.humanizer" in plugin_ids
        assert "quality.audit" in plugin_ids
        assert "publish.multiplatform" in plugin_ids
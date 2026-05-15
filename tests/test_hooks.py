from __future__ import annotations

import pytest
from iperson.pipeline.hook import BaseHook, HookContext, HookRegistry
from iperson.pipeline.context import PipelineContext


class TestTrendingInjectHook:
    @pytest.mark.asyncio
    async def test_trending_inject_adds_trending_to_context(self) -> None:
        from iperson.pipeline.hooks.trending_inject import TrendingInjectHook

        hook = TrendingInjectHook()
        assert hook.hook_id == "intelligence.trending_inject"
        assert hook.hook_point == "before.generation"

        pctx = PipelineContext(topic="AI 技术")
        ctx = HookContext(
            pipeline_ctx=pctx, hook_point="before.generation", config={}
        )
        result = await hook.execute(ctx)
        assert "trending_data" in result.pipeline_ctx.data


class TestBuiltinHooksRegistration:
    def test_register_builtin_hooks(self) -> None:
        from iperson.pipeline.hooks import register_builtin_hooks

        registry = HookRegistry()
        register_builtin_hooks(registry)
        listed = registry.list_hooks()
        hook_ids = [h["hook_id"] for h in listed]
        assert "intelligence.trending_inject" in hook_ids


class TestPromptGuardHook:
    @pytest.mark.asyncio
    async def test_prompt_guard_blocks_flagged_content(self) -> None:
        from iperson.pipeline.hooks.prompt_guard import PromptGuardHook

        hook = PromptGuardHook()
        pctx = PipelineContext(topic="test")
        pctx.data["persona_engine"] = None
        ctx = HookContext(
            pipeline_ctx=pctx, hook_point="before.generation", config={}
        )
        result = await hook.execute(ctx)
        assert "guard_triggered" in result.pipeline_ctx.data


class TestContentScanHook:
    @pytest.mark.asyncio
    async def test_content_scan_detects_banned_words(self) -> None:
        from iperson.pipeline.hooks.content_scan import ContentScanHook

        hook = ContentScanHook()
        pctx = PipelineContext(topic="test")
        pctx.generated_content = "总的来说，这是一个毋庸置疑的好产品"
        ctx = HookContext(
            pipeline_ctx=pctx, hook_point="after.generation", config={}
        )
        result = await hook.execute(ctx)
        assert "scan_result" in result.pipeline_ctx.data
        assert result.pipeline_ctx.data["scan_result"]["banned_found"]


class TestSecurityWordlist:
    def test_load_blocked_words(self) -> None:
        from iperson.core.security.wordlist import load_blocked_words

        words = load_blocked_words()
        assert isinstance(words, list)
        assert "总的来说" in words


class TestSeoAnalyzeHook:
    @pytest.mark.asyncio
    async def test_seo_analyze_generates_report(self) -> None:
        from iperson.pipeline.hooks.seo_analyze import SeoAnalyzeHook

        hook = SeoAnalyzeHook()
        pctx = PipelineContext(topic="test")
        pctx.generated_content = "# 标题\n\n这是一段正文内容，包含一些关键词。"
        ctx = HookContext(
            pipeline_ctx=pctx, hook_point="after.generation", config={}
        )
        result = await hook.execute(ctx)
        assert "seo_report" in result.pipeline_ctx.data
        report = result.pipeline_ctx.data["seo_report"]
        assert "word_count" in report
        assert "readability_score" in report
        assert "suggestions" in report
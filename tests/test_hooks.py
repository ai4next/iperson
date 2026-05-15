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
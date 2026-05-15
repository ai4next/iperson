from __future__ import annotations

import pytest
from iperson.pipeline.hook import BaseHook, HookContext, HookRegistry
from iperson.pipeline.context import PipelineContext


class TestHookBase:
    def test_hook_context_creation(self) -> None:
        ctx = HookContext(
            pipeline_ctx=PipelineContext(topic="test"),
            hook_point="before.generation",
            config={"key": "value"},
        )
        assert ctx.hook_point == "before.generation"
        assert ctx.config["key"] == "value"

    def test_hook_registry_register_and_get(self) -> None:
        registry = HookRegistry()

        class MyHook(BaseHook):
            hook_id = "test.my_hook"
            hook_point = "before.generation"
            name = "My Hook"

            async def execute(self, ctx: HookContext) -> HookContext:
                return ctx

        registry.register(MyHook)
        hooks = registry.get_hooks_for_point("before.generation")
        assert len(hooks) == 1
        assert hooks[0] == MyHook

    def test_hook_registry_empty_point(self) -> None:
        registry = HookRegistry()
        hooks = registry.get_hooks_for_point("nonexistent")
        assert hooks == []

    def test_hook_registry_list_hooks(self) -> None:
        registry = HookRegistry()

        class HookA(BaseHook):
            hook_id = "test.a"
            hook_point = "before.generation"
            name = "Hook A"

            async def execute(self, ctx: HookContext) -> HookContext:
                return ctx

        registry.register(HookA)
        listed = registry.list_hooks()
        assert any(h["hook_id"] == "test.a" for h in listed)


class TestHookOrchestrator:
    @pytest.mark.asyncio
    async def test_execute_hooks_runs_all_hooks_for_point(self) -> None:
        from iperson.pipeline.hook_orchestrator import HookOrchestrator

        registry = HookRegistry()

        class TraceHook(BaseHook):
            hook_id = "test.trace"
            hook_point = "before.generation"
            name = "Trace"

            async def execute(self, ctx: HookContext) -> HookContext:
                ctx.pipeline_ctx.data["trace"] = (
                    ctx.pipeline_ctx.data.get("trace", "") + "A"
                )
                return ctx

        registry.register(TraceHook)
        orch = HookOrchestrator(registry)

        pctx = PipelineContext(topic="test")
        result = await orch.execute_hooks("before.generation", pctx, {})
        assert result.data["trace"] == "A"

    @pytest.mark.asyncio
    async def test_execute_hooks_multiple_hooks_in_order(self) -> None:
        from iperson.pipeline.hook_orchestrator import HookOrchestrator

        registry = HookRegistry()

        class HookA(BaseHook):
            hook_id = "test.a"
            hook_point = "before.generation"
            name = "A"

            async def execute(self, ctx: HookContext) -> HookContext:
                ctx.pipeline_ctx.data["order"] = (
                    ctx.pipeline_ctx.data.get("order", "") + "A"
                )
                return ctx

        class HookB(BaseHook):
            hook_id = "test.b"
            hook_point = "before.generation"
            name = "B"

            async def execute(self, ctx: HookContext) -> HookContext:
                ctx.pipeline_ctx.data["order"] = (
                    ctx.pipeline_ctx.data.get("order", "") + "B"
                )
                return ctx

        registry.register(HookA)
        registry.register(HookB)
        orch = HookOrchestrator(registry)

        pctx = PipelineContext(topic="test")
        result = await orch.execute_hooks("before.generation", pctx, {})
        assert result.data["order"] == "AB"

    @pytest.mark.asyncio
    async def test_execute_hooks_empty_point_returns_unchanged(self) -> None:
        from iperson.pipeline.hook_orchestrator import HookOrchestrator

        registry = HookRegistry()
        orch = HookOrchestrator(registry)

        pctx = PipelineContext(topic="test")
        result = await orch.execute_hooks("nonexistent", pctx, {})
        assert result.topic == "test"
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
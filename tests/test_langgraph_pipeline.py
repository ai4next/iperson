"""Tests for LangGraph-based pipeline orchestration."""

from __future__ import annotations

from typing import Any

import pytest

from iperson.pipeline.context import PipelineContext
from iperson.pipeline.graph import build_pipeline_graph, run_pipeline
from iperson.pipeline.plugin import StagePlugin
from iperson.pipeline.registry import PluginRegistry
from iperson.pipeline.hook import BaseHook, HookContext, HookRegistry
from iperson.pipeline.state import PipelineState


SAMPLE_PIPELINE = {
    "name": "test",
    "nodes": [
        {"id": "step1", "node": "test.stage_one", "config": {}},
        {"id": "step2", "node": "test.stage_two", "config": {}},
    ],
}


class StageOne(StagePlugin):
    plugin_id = "test.stage_one"
    name = "Stage One"
    category = "generation"

    async def execute(
        self, ctx: PipelineContext, config: dict[str, Any] | None = None
    ) -> PipelineContext:
        ctx.data["stage_one_done"] = True
        ctx.generated_content = "hello from stage one"
        return ctx


class StageTwo(StagePlugin):
    plugin_id = "test.stage_two"
    name = "Stage Two"
    category = "quality"

    async def execute(
        self, ctx: PipelineContext, config: dict[str, Any] | None = None
    ) -> PipelineContext:
        ctx.data["stage_two_done"] = True
        ctx.generated_content = ctx.generated_content.upper()
        return ctx


@pytest.fixture
def registry() -> PluginRegistry:
    r = PluginRegistry()
    r.register(StageOne)
    r.register(StageTwo)
    return r


@pytest.fixture
def hook_registry() -> HookRegistry:
    return HookRegistry()


@pytest.mark.asyncio
async def test_build_and_run_pipeline(registry: PluginRegistry, hook_registry: HookRegistry) -> None:
    initial: PipelineState = {
        "status": "running",
        "data": {},
        "errors": [],
    }
    result = await run_pipeline(SAMPLE_PIPELINE, registry, hook_registry, initial)
    assert result["data"]["stage_one_done"] is True
    assert result["data"]["stage_two_done"] is True
    assert result["generated_content"] == "HELLO FROM STAGE ONE"


@pytest.mark.asyncio
async def test_add_hook_modifies_state(registry: PluginRegistry) -> None:
    class TestHook(BaseHook):
        hook_id = "test.uppercase"
        hook_point = "after.test.stage_one"
        name = "Uppercase Hook"

        async def execute(self, ctx: HookContext) -> HookContext:
            content = ctx.pipeline_ctx.generated_content
            ctx.pipeline_ctx.generated_content = content.upper() + " HOOKED"
            return ctx

    hook_registry = HookRegistry()
    hook_registry.register(TestHook)

    initial: PipelineState = {"status": "running", "data": {}, "errors": []}
    result = await run_pipeline(SAMPLE_PIPELINE, registry, hook_registry, initial)
    assert "HOOKED" in result["generated_content"]
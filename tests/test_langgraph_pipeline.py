"""Tests for LangGraph-based pipeline orchestration with agent nodes."""

from __future__ import annotations

from typing import Any

import pytest

from iperson.pipeline.agent_node import DeepAgentNode
from iperson.pipeline.graph import run_pipeline
from iperson.pipeline.hook import BaseHook, HookContext, HookRegistry
from iperson.pipeline.state import PipelineState


SAMPLE_PIPELINE = {
    "nodes": [
        {"id": "step1", "agent": {"prompt": "test.md", "model": None, "skills": []}},
        {"id": "step2", "agent": {"prompt": "test.md", "model": None, "skills": []}},
    ],
}


def _make_fake_ainvoke(output_key: str, output_value: Any) -> Any:
    """Create a fake agent_ainvoke that returns a JSON output."""

    async def fake_ainvoke(inputs: dict) -> dict:
        from langchain_core.messages import AIMessage

        return {
            "messages": [AIMessage(content=f'{{"{output_key}": "{output_value}"}}')],
        }

    return fake_ainvoke


def fake_agent_factory(nid: str, cfg: dict, hook_orch: Any) -> DeepAgentNode:
    """Create a DeepAgentNode that produces deterministic output."""
    if nid == "step1":
        node = DeepAgentNode(
            "step1",
            _make_fake_ainvoke("generated_content", "hello from step one"),
            "prompt",
            ["generated_content"],
        )
        # Store reference so tests can check data
        node._test_data = {}
        return node
    if nid == "step2":
        return DeepAgentNode(
            "step2",
            _make_fake_ainvoke("generated_content", "HELLO FROM STEP ONE"),
            "prompt",
            ["generated_content"],
        )
    msg = f"Unknown node: {nid}"
    raise ValueError(msg)


@pytest.fixture
def hook_registry() -> HookRegistry:
    return HookRegistry()


@pytest.mark.asyncio
async def test_build_and_run_pipeline(hook_registry: HookRegistry) -> None:
    initial: PipelineState = {"status": "running", "data": {}, "errors": []}
    result = await run_pipeline(
        SAMPLE_PIPELINE,
        hook_registry,
        initial,
        agent_factory=fake_agent_factory,
    )
    assert result["generated_content"] == "HELLO FROM STEP ONE"


@pytest.mark.asyncio
async def test_add_hook_modifies_state(hook_registry: HookRegistry) -> None:
    class TestHook(BaseHook):
        hook_id = "test.tracker"
        hook_point = "after.step1"
        name = "Tracker"

        async def execute(self, ctx: HookContext) -> HookContext:
            ctx.pipeline_ctx.data["hook_ran"] = True
            return ctx

    hook_registry.register(TestHook)

    initial: PipelineState = {"status": "running", "data": {}, "errors": []}
    result = await run_pipeline(
        SAMPLE_PIPELINE,
        hook_registry,
        initial,
        agent_factory=fake_agent_factory,
    )
    assert result["data"]["hook_ran"] is True
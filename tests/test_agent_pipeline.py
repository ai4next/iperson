"""Integration tests for agent-based pipeline nodes."""

from __future__ import annotations

from typing import Any

import pytest

from iperson.pipeline.state import PipelineState


class FakeAgent:
    """Deterministic fake deep agent for testing."""

    def __init__(self, output_text: str) -> None:
        self.output_text = output_text

    async def ainvoke(self, inputs: dict) -> dict:
        from langchain_core.messages import AIMessage

        return {
            "messages": [AIMessage(content=self.output_text)],
        }


@pytest.mark.asyncio
async def test_agent_node_updates_pipeline_state() -> None:
    """An agent that returns JSON should update PipelineState fields."""
    from iperson.pipeline.agent_node import DeepAgentNode

    agent = FakeAgent('```json\n{"generated_content": "Hello world"}\n```')
    node = DeepAgentNode(
        node_id="test",
        agent_ainvoke=agent.ainvoke,
        system_prompt="test",
    )

    state: PipelineState = PipelineState(
        status="running",
        kb_chunks=[],
        kb_context="",
        topic="test",
        generated_content="",
        platform_contents={},
        publish_results=[],
        errors=[],
        data={},
    )

    result = await node(state)
    assert result["generated_content"] == "Hello world"


@pytest.mark.asyncio
async def test_agent_node_handles_invalid_json() -> None:
    """Non-JSON agent response should be stored as raw fallback."""
    from iperson.pipeline.agent_node import DeepAgentNode

    agent = FakeAgent("Just a plain text response without JSON")
    node = DeepAgentNode(
        node_id="test",
        agent_ainvoke=agent.ainvoke,
        system_prompt="test",
    )

    state: PipelineState = PipelineState(
        status="running",
        kb_chunks=[],
        kb_context="",
        topic="t",
        generated_content="",
        platform_contents={},
        publish_results=[],
        errors=[],
        data={},
    )

    result = await node(state)
    assert result["data"]["test_raw_response"] == "Just a plain text response without JSON"
    assert result["status"] == "running"


@pytest.mark.asyncio
async def test_agent_node_with_hooks_via_graph() -> None:
    """Agent node should work when wrapped with hook lifecycle in graph.py."""
    from iperson.pipeline.agent_node import DeepAgentNode
    from iperson.pipeline.context import PipelineContext
    from iperson.pipeline.hook import HookContext, BaseHook

    # Track hook execution
    hook_calls: list[str] = []

    class BeforeHook(BaseHook):
        hook_id = "test.before"
        hook_point = "before.test"
        name = "Before"
        description = "Tracks before hook"

        async def execute(self, ctx: HookContext) -> HookContext:
            hook_calls.append(ctx.hook_point)
            ctx.pipeline_ctx.data["before_ran"] = True
            return ctx

    class AfterHook(BaseHook):
        hook_id = "test.after"
        hook_point = "after.test"
        name = "After"
        description = "Tracks after hook"

        async def execute(self, ctx: HookContext) -> HookContext:
            hook_calls.append(ctx.hook_point)
            return ctx

    from iperson.pipeline.hook import HookRegistry
    from iperson.pipeline.hook_orchestrator import HookOrchestrator

    registry = HookRegistry()
    registry.register(BeforeHook)
    registry.register(AfterHook)
    orch = HookOrchestrator(registry)

    # Build agent node via the graph.py helper logic
    agent = FakeAgent('```json\n{"generated_content": "hook test"}\n```')
    agent_node = DeepAgentNode(
        node_id="test",
        agent_ainvoke=agent.ainvoke,
        system_prompt="test",
    )

    # Simulate what graph.py does: state→ctx→hooks→state→agent→state→ctx→hooks
    state: PipelineState = PipelineState(
        status="running",
        kb_chunks=[],
        kb_context="",
        topic="test",
        generated_content="",
        platform_contents={},
        publish_results=[],
        errors=[],
        data={},
    )

    ctx = PipelineContext(topic=state["topic"])
    ctx.status = state["status"]
    ctx.kb_chunks = state["kb_chunks"]
    ctx.kb_context = state["kb_context"]
    ctx.generated_content = state["generated_content"]
    ctx.platform_contents = state["platform_contents"]
    ctx.errors = state["errors"]
    ctx.data = state.get("data", {})

    ctx = await orch.execute_hooks("before.test", ctx, {})
    state["data"] = ctx.data

    state = await agent_node(state)

    ctx = PipelineContext(topic=state["topic"])
    ctx.status = state["status"]
    ctx.generated_content = state["generated_content"]
    ctx.data = state.get("data", {})

    ctx = await orch.execute_hooks("after.test", ctx, {})

    assert "before.test" in hook_calls
    assert "after.test" in hook_calls
    assert state["data"].get("before_ran") is True
    assert state["generated_content"] == "hook test"
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langgraph.graph import StateGraph, END

from iperson.pipeline.state import PipelineState
from iperson.pipeline.context import PipelineContext
from iperson.pipeline.plugin import StagePlugin
from iperson.pipeline.registry import PluginRegistry
from iperson.pipeline.hook import HookRegistry
from iperson.pipeline.hook_orchestrator import HookOrchestrator
from iperson.pipeline.agent_factory import build_agent_node


def _build_hook_config(node_def: dict[str, Any]) -> dict[str, Any]:
    """Extract hook config from a node definition."""
    hook_config: dict[str, Any] = {"before": {}, "after": {}}
    hooks = node_def.get("hooks", {})
    for point in ("before", "after"):
        for hook_entry in hooks.get(point, []):
            hook_id = hook_entry.get("hook", "")
            hook_config[point][hook_id] = hook_entry.get("config", {})
    return hook_config


def _create_node_fn(
    plugin_id: str,
    plugin_class: type[StagePlugin],
    node_def: dict[str, Any],
    hook_orch: HookOrchestrator,
) -> Callable[[PipelineState], PipelineState]:
    """Create a LangGraph node function that executes the plugin with hooks."""

    async def node_fn(state: PipelineState) -> dict[str, Any]:
        ctx = _state_to_context(state)
        stage_config = node_def.get("config", {})

        # Pre-hooks
        ctx = await hook_orch.execute_hooks(f"before.{plugin_id}", ctx, node_def)

        # Node execution
        instance = plugin_class()
        ctx = await instance.execute(ctx, stage_config)

        # Post-hooks
        ctx = await hook_orch.execute_hooks(f"after.{plugin_id}", ctx, node_def)

        return _context_to_state(ctx)

    return node_fn


def _create_agent_node_fn(
    node_def: dict[str, Any],
    hook_orch: HookOrchestrator,
    agent_factory: Callable,
) -> Callable[[PipelineState], PipelineState]:
    """Create a LangGraph node function that runs a deep agent node with hooks."""
    agent_node = agent_factory(node_def["id"], node_def["agent"], hook_orch)

    async def agent_node_fn(state: PipelineState) -> dict[str, Any]:
        ctx = _state_to_context(state)
        ctx = await hook_orch.execute_hooks(f"before.{node_def['id']}", ctx, node_def)
        state = _context_to_state(ctx)
        state = await agent_node(state)
        ctx = _state_to_context(state)
        ctx = await hook_orch.execute_hooks(f"after.{node_def['id']}", ctx, node_def)
        return _context_to_state(ctx)

    return agent_node_fn


def _state_to_context(state: PipelineState) -> PipelineContext:
    """Convert PipelineState to PipelineContext for backward compat."""
    ctx = PipelineContext(
        topic=state.get("topic", ""),
    )
    ctx.kb_chunks = state.get("kb_chunks", [])
    ctx.kb_context = state.get("kb_context", "")
    ctx.generated_content = state.get("generated_content", "")
    ctx.platform_contents = state.get("platform_contents", {})
    ctx.data = state.get("data", {})
    ctx.errors = state.get("errors", [])
    ctx.status = state.get("status", "running")
    return ctx


def _context_to_state(ctx: PipelineContext) -> dict[str, Any]:
    """Convert PipelineContext back to dict for state update."""
    return {
        "kb_chunks": ctx.kb_chunks,
        "kb_context": ctx.kb_context,
        "topic": ctx.topic,
        "generated_content": ctx.generated_content,
        "platform_contents": ctx.platform_contents,
        "publish_results": ctx.publish_results,
        "data": ctx.data,
        "errors": ctx.errors,
        "status": ctx.status,
    }


def build_pipeline_graph(
    pipeline: dict[str, Any],
    plugin_registry: PluginRegistry,
    hook_registry: HookRegistry,
    agent_factory: Callable | None = None,
) -> StateGraph:
    """Build a LangGraph StateGraph from a pipeline definition."""
    hook_orch = HookOrchestrator(hook_registry)
    workflow = StateGraph(PipelineState)

    nodes_def: list[dict[str, Any]] = pipeline.get("nodes", [])
    node_ids: list[str] = []

    for node_def in nodes_def:
        node_id = node_def["id"]
        if "agent" in node_def and agent_factory is not None:
            node_fn = _create_agent_node_fn(node_def, hook_orch, agent_factory)
        else:
            plugin_id = node_def["node"]
            plugin_class = plugin_registry.get(plugin_id)
            node_fn = _create_node_fn(plugin_id, plugin_class, node_def, hook_orch)
        workflow.add_node(node_id, node_fn)
        node_ids.append(node_id)

    if not node_ids:
        # No nodes to execute; add a passthrough node
        workflow.add_node("noop", lambda s: s)
        workflow.set_entry_point("noop")
        workflow.add_edge("noop", END)
        return workflow

    # Add edges: chain nodes sequentially
    for i in range(len(node_ids) - 1):
        workflow.add_edge(node_ids[i], node_ids[i + 1])

    workflow.set_entry_point(node_ids[0])
    workflow.add_edge(node_ids[-1], END)

    return workflow


async def run_pipeline(
    pipeline: dict[str, Any],
    plugin_registry: PluginRegistry,
    hook_registry: HookRegistry,
    initial_state: PipelineState,
    agent_factory: Callable | None = None,
) -> PipelineState:
    """Build and run a pipeline graph."""
    graph = build_pipeline_graph(pipeline, plugin_registry, hook_registry, agent_factory)
    app = graph.compile()
    result: PipelineState = await app.ainvoke(initial_state)
    return result
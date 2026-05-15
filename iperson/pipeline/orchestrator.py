from __future__ import annotations

from typing import Any

from iperson.pipeline.context import PipelineContext
from iperson.pipeline.graph import run_pipeline
from iperson.pipeline.hook import HookRegistry
from iperson.pipeline.registry import PluginRegistry
from iperson.pipeline.state import PipelineState


class PipelineOrchestrator:
    """Orchestrates pipeline execution via LangGraph."""

    def __init__(
        self,
        registry: PluginRegistry,
        hook_registry: HookRegistry | None = None,
    ) -> None:
        self.registry = registry
        self.hook_registry = hook_registry or HookRegistry()

    async def run(self, ctx: PipelineContext, pipeline: dict[str, Any]) -> PipelineContext:
        """Execute all pipeline nodes via LangGraph."""
        initial_state: PipelineState = {
            "status": "running",
            "kb_context": ctx.kb_context,
            "topic": ctx.topic,
            "generated_content": ctx.generated_content,
            "platform_contents": ctx.platform_contents,
            "data": ctx.data,
            "errors": ctx.errors,
        }

        final_state = await run_pipeline(
            pipeline=pipeline,
            plugin_registry=self.registry,
            hook_registry=self.hook_registry,
            initial_state=initial_state,
        )

        # Write state back to context
        ctx.kb_context = final_state.get("kb_context", "")
        ctx.topic = final_state.get("topic", "")
        ctx.generated_content = final_state.get("generated_content", "")
        ctx.platform_contents = final_state.get("platform_contents", {})
        ctx.data = final_state.get("data", {})
        ctx.errors = final_state.get("errors", [])
        ctx.status = final_state.get("status", "completed")
        return ctx
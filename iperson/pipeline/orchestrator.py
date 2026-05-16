from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from iperson.pipeline.context import PipelineContext
from iperson.pipeline.graph import run_pipeline
from iperson.pipeline.hook import HookRegistry
from iperson.pipeline.registry import PluginRegistry
from iperson.pipeline.state import PipelineState
from iperson.core.persona.engine import PersonaEngine
from iperson.pipeline.agent_factory import build_agent_node


class PipelineOrchestrator:
    """Orchestrates pipeline execution via LangGraph."""

    def __init__(
        self,
        registry: PluginRegistry,
        hook_registry: HookRegistry | None = None,
    ) -> None:
        self.registry = registry
        self.hook_registry = hook_registry or HookRegistry()

    async def _auto_select_topic(self, ctx: PipelineContext, pipeline: dict[str, Any]) -> PipelineContext:
        """Select a topic from KB context or LLM knowledge using persona."""
        persona_engine: PersonaEngine | None = ctx.data.get("persona_engine")
        if persona_engine is None:
            ctx.errors.append({
                "error_code": "TOPIC_SELECTION_FAILED",
                "stage": "topic_selection",
                "message": "No persona engine found in context for topic selection.",
                "recoverable": False,
            })
            ctx.status = "completed_with_errors"
            return ctx

        llm = ctx.data.get("llm_client")
        if llm is None:
            ctx.errors.append({
                "error_code": "TOPIC_SELECTION_FAILED",
                "stage": "topic_selection",
                "message": "No LLM client available for topic selection.",
                "recoverable": False,
            })
            ctx.status = "completed_with_errors"
            return ctx

        if ctx.kb_context:
            prompt = (
                f"你是一位内容选题助手。以下是人设信息：\n"
                f"---\n"
                f"{persona_engine.build_system_prompt()}\n"
                f"---\n"
                f"以下是知识库素材：\n"
                f"---\n"
                f"{ctx.kb_context}\n"
                f"---\n"
                f"请从以上素材中，选择一个最符合上述人设的创作选题。\n"
                f"只输出选题标题，不要多余内容。"
            )
        else:
            prompt = (
                f"你是一位内容选题助手。以下是人设信息：\n"
                f"---\n"
                f"{persona_engine.build_system_prompt()}\n"
                f"---\n"
                f"请结合你的知识储备，为该人设推荐一个适合创作的内容选题。\n"
                f"选题应贴合人设定位，具有吸引力和传播力。\n"
                f"只输出选题标题，不要多余内容。"
            )

        messages = [{"role": "user", "content": prompt}]
        response = await llm.ainvoke(messages)
        topic = response.content.strip()

        if not topic:
            ctx.errors.append({
                "error_code": "TOPIC_SELECTION_FAILED",
                "stage": "topic_selection",
                "message": "LLM returned empty topic during auto selection.",
                "recoverable": True,
            })
            return ctx

        ctx.topic = topic
        return ctx

    async def run(self, ctx: PipelineContext, pipeline: dict[str, Any]) -> PipelineContext:
        """Execute all pipeline nodes via LangGraph."""
        # Auto topic selection (built-in, runs before nodes)
        if pipeline.get("topic_selection") and not ctx.topic:
            ctx = await self._auto_select_topic(ctx, pipeline)
            if ctx.errors:
                ctx.completed_at = datetime.now(timezone.utc).isoformat()
                return ctx

        initial_state: PipelineState = {
            "status": "running",
            "kb_chunks": ctx.kb_chunks,
            "kb_context": ctx.kb_context,
            "topic": ctx.topic,
            "generated_content": ctx.generated_content,
            "platform_contents": ctx.platform_contents,
            "publish_results": ctx.publish_results,
            "data": ctx.data,
            "errors": ctx.errors,
        }

        final_state = await run_pipeline(
            pipeline=pipeline,
            plugin_registry=self.registry,
            hook_registry=self.hook_registry,
            initial_state=initial_state,
            agent_factory=build_agent_node,
        )

        # Write state back to context
        ctx.kb_chunks = final_state.get("kb_chunks", [])
        ctx.kb_context = final_state.get("kb_context", "")
        ctx.topic = final_state.get("topic", "")
        ctx.generated_content = final_state.get("generated_content", "")
        ctx.platform_contents = final_state.get("platform_contents", {})
        ctx.publish_results = final_state.get("publish_results", [])
        ctx.data = final_state.get("data", {})
        ctx.errors = final_state.get("errors", [])
        ctx.status = "completed"
        ctx.completed_at = datetime.now(timezone.utc).isoformat()
        return ctx
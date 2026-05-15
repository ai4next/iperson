from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from iperson.pipeline.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
)
from iperson.pipeline.context import PipelineContext
from iperson.pipeline.errors import PipelineError
from iperson.pipeline.plugin import StagePlugin
from iperson.pipeline.registry import PluginRegistry
from iperson.pipeline.hook import HookRegistry
from iperson.pipeline.hook_orchestrator import HookOrchestrator
from iperson.core.persona.engine import PersonaEngine


class PipelineOrchestrator:
    """Orchestrates sequential execution of pipeline stages with CircuitBreaker support."""

    def __init__(
        self,
        registry: PluginRegistry,
        hook_registry: HookRegistry | None = None,
    ) -> None:
        self.registry = registry
        self.hook_orch = HookOrchestrator(hook_registry or HookRegistry())
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

    def _get_circuit_breaker(self, plugin_id: str) -> CircuitBreaker:
        if plugin_id not in self.circuit_breakers:
            cb_config = CircuitBreakerConfig()
            self.circuit_breakers[plugin_id] = CircuitBreaker(cb_config)
        return self.circuit_breakers[plugin_id]

    async def _auto_select_topic(self, ctx: PipelineContext, pipeline: dict[str, Any]) -> PipelineContext:
        """Select a topic from KB context using persona and LLM."""
        if not ctx.kb_context:
            ctx.errors.append(PipelineError(
                error_code="TOPIC_SELECTION_FAILED",
                stage="topic_selection",
                message="No KB context available for topic selection. Import KB docs first.",
                recoverable=False,
            ))
            ctx.status = "completed_with_errors"
            return ctx

        persona_engine: PersonaEngine | None = ctx.data.get("persona_engine")
        if persona_engine is None:
            ctx.errors.append(PipelineError(
                error_code="TOPIC_SELECTION_FAILED",
                stage="topic_selection",
                message="No persona engine found in context for topic selection.",
                recoverable=False,
            ))
            ctx.status = "completed_with_errors"
            return ctx

        llm = ctx.data.get("llm_client")
        if llm is None:
            ctx.errors.append(PipelineError(
                error_code="TOPIC_SELECTION_FAILED",
                stage="topic_selection",
                message="No LLM client available for topic selection.",
                recoverable=False,
            ))
            ctx.status = "completed_with_errors"
            return ctx

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

        messages = [{"role": "user", "content": prompt}]
        response = await llm.ainvoke(messages)
        topic = response.content.strip()

        if not topic:
            ctx.errors.append(PipelineError(
                error_code="TOPIC_SELECTION_FAILED",
                stage="topic_selection",
                message="LLM returned empty topic during auto selection.",
                recoverable=True,
            ))
            return ctx

        ctx.topic = topic
        return ctx

    async def run(self, ctx: PipelineContext, pipeline: dict[str, Any]) -> PipelineContext:
        """Execute all stages with circuit breaker and error strategy."""
        stages: list[dict[str, Any]] = pipeline.get("stages", [])

        # Pre-validation: check all plugin_ids exist
        for stage_def in stages:
            plugin_id = stage_def.get("plugin", "")
            if not plugin_id:
                ctx.errors.append(PipelineError(
                    error_code="INVALID_STAGE",
                    stage="unknown",
                    message="Stage missing 'plugin' field",
                    recoverable=False,
                ))
                return ctx
            if not self.registry.has(plugin_id):
                ctx.errors.append(PipelineError(
                    error_code="PLUGIN_NOT_FOUND",
                    stage=plugin_id,
                    message=f"Unknown plugin: '{plugin_id}'",
                    recoverable=True,
                ))
                return ctx

        # Auto topic selection (built-in, runs before stages)
        if pipeline.get("topic_selection") and not ctx.topic:
            ctx = await self._auto_select_topic(ctx, pipeline)
            if ctx.errors:
                return ctx

        for stage_def in stages:
            plugin_id: str = stage_def["plugin"]
            stage_config: dict[str, Any] = stage_def.get("config", {})
            max_retries: int = int(stage_config.get("max_retries", 0))
            on_error: str = stage_config.get("on_error", "abort")

            # Circuit breaker check
            cb = self._get_circuit_breaker(plugin_id)
            try:
                cb.check()
            except CircuitBreakerError:
                ctx.errors.append(PipelineError(
                    error_code="CIRCUIT_OPEN",
                    stage=plugin_id,
                    message=f"Circuit breaker is OPEN for plugin '{plugin_id}'",
                    recoverable=on_error != "abort",
                ))
                if on_error == "abort":
                    break
                continue

            # Before hooks
            ctx = await self.hook_orch.execute_hooks(f"before.{plugin_id}", ctx, stage_config)

            plugin_class = self.registry.get(plugin_id)
            plugin_instance: StagePlugin = plugin_class()

            attempt = 0
            last_exc: Exception | None = None
            while attempt <= max_retries:
                try:
                    start = time.monotonic()
                    ctx = await plugin_instance.execute(ctx, stage_config)
                    elapsed = time.monotonic() - start
                    ctx.data[f"_timing_{plugin_id}"] = elapsed
                    cb.record_success()
                    last_exc = None
                    break
                except Exception as exc:
                    attempt += 1
                    last_exc = exc
                    cb.record_failure()

            if last_exc is not None:
                ctx.errors.append(PipelineError(
                    error_code="STAGE_FAILED",
                    stage=plugin_id,
                    message=str(last_exc),
                    recoverable=on_error != "abort",
                    attempts=attempt,
                ))
                if on_error == "abort":
                    break

            # After hooks
            ctx = await self.hook_orch.execute_hooks(f"after.{plugin_id}", ctx, stage_config)

        ctx.completed_at = datetime.now(timezone.utc).isoformat()
        if not ctx.errors:
            ctx.status = "completed"
        else:
            ctx.status = "completed_with_errors"

        return ctx
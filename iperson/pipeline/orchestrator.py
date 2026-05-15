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
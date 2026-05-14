from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from iperson.pipeline.context import PipelineContext
from iperson.pipeline.plugin import StagePlugin
from iperson.pipeline.registry import PluginRegistry


class PipelineOrchestrator:
    """Orchestrates sequential execution of pipeline stages."""

    def __init__(self, registry: PluginRegistry) -> None:
        self.registry = registry

    async def run(self, ctx: PipelineContext, recipe: dict[str, Any]) -> PipelineContext:
        """Execute all stages in the recipe sequentially.

        For each stage:
          1. Look up the plugin in the registry.
          2. Instantiate and execute it.
          3. Track timing and handle errors.
          4. On failure, respect max_retries config.
        """
        stages: list[dict[str, Any]] = recipe.get("stages", [])

        for stage_def in stages:
            plugin_id: str = stage_def["plugin"]
            stage_config: dict[str, Any] = stage_def.get("config", {})
            max_retries: int = int(stage_config.get("max_retries", 0))

            if not self.registry.has(plugin_id):
                ctx.errors.append({
                    "stage": plugin_id,
                    "error": f"Unknown plugin: '{plugin_id}'",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                continue

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
                    last_exc = None
                    break  # success, move to next stage
                except Exception as exc:
                    attempt += 1
                    last_exc = exc

            if last_exc is not None:
                ctx.errors.append({
                    "stage": plugin_id,
                    "error": str(last_exc),
                    "attempts": attempt,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })

        ctx.completed_at = datetime.now(timezone.utc).isoformat()
        if not ctx.errors:
            ctx.status = "completed"
        else:
            ctx.status = "completed_with_errors"

        return ctx
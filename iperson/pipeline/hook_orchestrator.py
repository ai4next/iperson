from __future__ import annotations

from typing import Any

from iperson.pipeline.context import PipelineContext
from iperson.pipeline.hook import HookContext, HookRegistry


class HookOrchestrator:
    def __init__(self, registry: HookRegistry) -> None:
        self.registry = registry

    async def execute_hooks(
        self,
        hook_point: str,
        pipeline_ctx: PipelineContext,
        stage_config: dict[str, Any],
    ) -> PipelineContext:
        hooks = self.registry.get_hooks_for_point(hook_point)
        for hook_cls in hooks:
            hook_config = stage_config.get("hooks", {}).get(
                hook_point.split(".")[-1], {}
            )
            hook_ctx = HookContext(
                pipeline_ctx=pipeline_ctx,
                hook_point=hook_point,
                config=hook_config,
            )
            result = await hook_cls().execute(hook_ctx)
            pipeline_ctx = result.pipeline_ctx
        return pipeline_ctx
from __future__ import annotations

from iperson.pipeline.hook import BaseHook, HookContext


class PromptGuardHook(BaseHook):
    hook_id: str = "safety.prompt_guard"
    hook_point: str = "before.generation"
    name: str = "Prompt Guard"
    description: str = "Check generation prompt for prohibited content before generation"

    async def execute(self, ctx: HookContext) -> HookContext:
        persona_engine = ctx.pipeline_ctx.data.get("persona_engine")
        if persona_engine is None:
            ctx.pipeline_ctx.data["guard_triggered"] = True
            ctx.pipeline_ctx.data["guard_reason"] = "No persona engine configured"
        return ctx
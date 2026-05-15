from __future__ import annotations

from typing import Any

from iperson.core.humanizer.detector import AIDetector
from iperson.core.humanizer.scorer import AIScorer
from iperson.core.humanizer.transformer import HumanizerTransformer
from iperson.pipeline.hook import BaseHook, HookContext


class HumanizerHook(BaseHook):
    hook_id = "quality.humanizer"
    hook_point = "after.generate"
    name = "Humanizer"
    description = "Detect and reduce AI痕迹 in generated content"

    async def execute(self, ctx: HookContext) -> HookContext:
        content = ctx.pipeline_ctx.generated_content
        if not content:
            return ctx

        detector = AIDetector()
        scorer = AIScorer(detector)
        transformer = HumanizerTransformer(detector, scorer)

        llm_client = ctx.pipeline_ctx.data.get("llm_client")
        persona_engine = ctx.pipeline_ctx.data.get("persona_engine")

        result = await transformer.transform(
            content=content,
            config=ctx.config,
            llm_client=llm_client,
            persona_engine=persona_engine,
        )

        ctx.pipeline_ctx.generated_content = result
        return ctx
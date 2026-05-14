from __future__ import annotations

from typing import Any

from iperson.core.humanizer.detector import AIDetector
from iperson.core.humanizer.scorer import AIScorer
from iperson.core.humanizer.transformer import HumanizerTransformer
from iperson.pipeline.context import PipelineContext
from iperson.pipeline.plugin import StagePlugin


class HumanizerPlugin(StagePlugin):
    plugin_id = "quality.humanizer"

    async def execute(self, ctx: PipelineContext, config: dict[str, Any]) -> PipelineContext:
        if not ctx.generated_content:
            return ctx

        detector = AIDetector()
        scorer = AIScorer(detector)
        transformer = HumanizerTransformer(detector, scorer)

        llm_client = ctx.data.get("llm_client")
        persona_engine = ctx.data.get("persona_engine")

        result = await transformer.transform(
            content=ctx.generated_content,
            config=config,
            llm_client=llm_client,
            persona_engine=persona_engine,
        )

        ctx.humanized_content = result
        return ctx
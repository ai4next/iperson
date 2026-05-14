from __future__ import annotations

from typing import Any

from iperson.core.humanizer import humanize
from iperson.pipeline.context import PipelineContext
from iperson.pipeline.plugin import StagePlugin


class HumanizerPlugin(StagePlugin):
    """Humanize generated content by replacing AI-like phrasing."""

    plugin_id: str = "quality.humanizer"
    name: str = "Humanizer"
    description: str = "Replace AI-like phrasing with more natural alternatives"
    category: str = "quality"
    version: str = "1.0.0"
    default_config: dict[str, Any] = {
        "min_score": 0.35,
        "max_iterations": 2,
    }

    async def execute(
        self, ctx: PipelineContext, config: dict[str, Any] | None = None
    ) -> PipelineContext:
        """Run the humanizer pipeline on ``ctx.generated_content``.

        Config accepts:
            - ``min_score``: Score threshold to stop iterating (default 0.35).
            - ``max_iterations``: Maximum number of refinement cycles (default 2).

        Sets ``ctx.humanized_content`` and ``ctx.data["humanizer_result"]``.
        """
        content = ctx.generated_content
        if not content:
            ctx.humanized_content = None
            ctx.data["humanizer_result"] = {
                "text": None,
                "changes": [],
                "score": 0.0,
                "iterations": 0,
            }
            return ctx

        merged = {**self.default_config, **(config or {})}
        result = await humanize(
            content,
            min_score=merged["min_score"],
            max_iterations=merged["max_iterations"],
        )

        ctx.humanized_content = result["text"]
        ctx.data["humanizer_result"] = result

        return ctx
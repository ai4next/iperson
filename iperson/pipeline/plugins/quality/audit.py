from __future__ import annotations

from typing import Any

from iperson.core.audit.gate import AuditGate
from iperson.core.humanizer.scorer import score_ai_ness
from iperson.pipeline.context import PipelineContext
from iperson.pipeline.plugin import StagePlugin


class AuditPlugin(StagePlugin):
    """Run a 6-dimension quality audit on generated or humanized content."""

    plugin_id: str = "quality.audit"
    name: str = "Audit Gate"
    description: str = "Run a 6-dimension quality audit on content"
    category: str = "quality"
    version: str = "1.0.0"

    async def execute(
        self, ctx: PipelineContext, config: dict[str, Any] | None = None
    ) -> PipelineContext:
        """Evaluate content quality across six dimensions.

        Uses ``ctx.humanized_content`` if available, falls back to
        ``ctx.generated_content``.

        Reads keywords from ``ctx.data["keywords"]`` and platform from
        ``ctx.data["platform"]`` (defaults to ``"xiaohongshu"``).

        Sets ``ctx.audit_result``.
        """
        # Prefer humanized content, fall back to generated
        content = ctx.humanized_content or ctx.generated_content
        if not content:
            ctx.audit_result = {
                "overall_status": "skip",
                "scores": {},
                "dimensions": {},
                "summary": "No content to audit",
            }
            return ctx

        keywords: list[str] = ctx.data.get("keywords", [])
        platform: str = ctx.data.get("platform", "xiaohongshu")
        ai_score = score_ai_ness(content)

        gate = AuditGate()
        ctx.audit_result = gate.evaluate(
            content,
            keywords,
            platform=platform,
            kb_chunks=ctx.kb_chunks,
            ai_score=ai_score,
        )

        return ctx
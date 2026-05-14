from __future__ import annotations

from typing import Any

from iperson.core.audit.gate import AuditGate
from iperson.core.audit.grounding import check_grounding
from iperson.core.audit.keyword_check import check_keyword_fit
from iperson.core.audit.platform_rules import check_platform_rules
from iperson.core.audit.structure_check import check_structure
from iperson.core.humanizer.scorer import score_ai_ness
from iperson.pipeline.context import PipelineContext
from iperson.pipeline.plugin import StagePlugin


class AuditPlugin(StagePlugin):
    """Run a 6-dimension quality audit on generated or humanized content."""

    plugin_id: str = "quality.audit"
    name: str = "Audit Gate"
    description: str = "Run a 6-dimension quality audit on content"
    category: str = "quality"
    version: str = "2.0.0"

    async def execute(
        self, ctx: PipelineContext, config: dict[str, Any] | None = None
    ) -> PipelineContext:
        """Evaluate content quality across six dimensions.

        Uses ``ctx.humanized_content`` if available, falls back to
        ``ctx.generated_content``.

        Reads platform from ``ctx.data["platform"]`` (defaults to
        ``"xiaohongshu"``).

        Sets ``ctx.audit_result``.
        """
        # Prefer humanized content, fall back to generated
        content = ctx.humanized_content or ctx.generated_content
        if not content:
            ctx.audit_result = {
                "overall_status": "skip",
                "scores": {},
                "sub_scores": {},
                "suggestions": [],
                "summary": "No content to audit",
            }
            return ctx

        platform: str = ctx.data.get("platform", "xiaohongshu")
        ai_score_raw = score_ai_ness(content)

        # Run each check function independently
        grounding_result = check_grounding(content, ctx.kb_chunks or [])
        keyword_result = check_keyword_fit(content)
        structure_result = check_structure(content)
        platform_result = check_platform_rules(content, platform)

        # Style consistency from config or default
        style_score = 1.0  # default if not provided
        for key in ("style_score", "style_consistency"):
            val = ctx.data.get(key)
            if val is not None:
                style_score = float(val)
                break

        dimension_scores: dict[str, dict[str, Any]] = {
            "grounding": grounding_result,
            "keyword_fit": keyword_result,
            "structure": structure_result,
            "platform_rules": platform_result,
            "style_consistency": {
                "score": style_score,
                "sub_scores": {},
                "suggestions": (
                    ["风格一致性较低"] if style_score < 0.5 else []
                ),
            },
            "ai_score": {
                "score": ai_score_raw,
                "sub_scores": {},
                "suggestions": (
                    ["AI痕迹较重，建议增加人工润色"]
                    if ai_score_raw > 0.35
                    else []
                ),
            },
        }

        gate = AuditGate()
        ctx.audit_result = gate.evaluate(dimension_scores)

        return ctx
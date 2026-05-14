from __future__ import annotations

from typing import Any

from iperson.core.audit.grounding import check_grounding
from iperson.core.audit.keyword_check import check_keyword_fit
from iperson.core.audit.platform_rules import check_platform_rules
from iperson.core.audit.report import AuditReport
from iperson.core.audit.structure_check import check_structure
from iperson.core.humanizer.scorer import score_ai_ness


class AuditGate:
    """Orchestrates the 6-dimension quality audit for generated content.

    Dimensions:
        1. grounding — factual accuracy against KB
        2. keyword_fit — keyword presence
        3. structure — document structure quality
        4. platform_rules — platform-specific constraint compliance
        5. style_consistency — adherence to target style
        6. ai_score — AI-ness score (lower is better)
    """

    THRESHOLDS: dict[str, float] = {
        "grounding": 0.8,
        "keyword_fit": 0.7,
        "structure": 0.7,
        "platform_rules": 0.7,
        "style_consistency": 0.7,
        "ai_score": 0.35,
    }

    CRITICAL_DIMENSIONS: set[str] = {"grounding", "keyword_fit"}

    def evaluate(
        self,
        content: str,
        keywords: list[str],
        platform: str = "xiaohongshu",
        kb_chunks: list[dict] | None = None,
        style_score: float | None = None,
        ai_score: float | None = None,
    ) -> dict[str, Any]:
        """Run all 6 dimension checks and produce an audit report.

        Args:
            content: The text to audit.
            keywords: Target keywords for keyword fit check.
            platform: Target platform name (default "xiaohongshu").
            kb_chunks: KB chunks for grounding verification.
            style_score: Pre-computed style consistency score (0-1).
            ai_score: Pre-computed AI-ness score (0-1, lower is better).

        Returns:
            The AuditReport serialized as a dict.
        """
        content = content or ""

        report = AuditReport(content_id="audit-session")

        # Dimension 1: Grounding
        grounding_result = check_grounding(
            content, kb_chunks or []
        )
        report.add_dimension("grounding", grounding_result)

        # Dimension 2: Keyword fit
        keyword_result = check_keyword_fit(content, keywords)
        report.add_dimension("keyword_fit", keyword_result)

        # Dimension 3: Structure
        structure_result = check_structure(content)
        report.add_dimension("structure", structure_result)

        # Dimension 4: Platform rules
        platform_result = check_platform_rules(content, platform)
        report.add_dimension("platform_rules", platform_result)

        # Dimension 5: Style consistency
        style_actual = style_score if style_score is not None else 1.0
        report.add_dimension(
            "style_consistency",
            {"score": style_actual, "status": "pass" if style_actual >= 0.5 else "review"},
        )

        # Dimension 6: AI score
        ai_actual = ai_score if ai_score is not None else score_ai_ness(content)
        # Invert: low AI-ness is good, so we report as (1 - ai_actual)
        # But we store the raw score for transparency
        report.add_dimension(
            "ai_score",
            {"score": ai_actual, "status": "pass" if ai_actual <= 0.35 else "review"},
        )

        return report.to_dict()
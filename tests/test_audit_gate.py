from __future__ import annotations

from iperson.core.audit.gate import AuditGate, check_gate, compute_weighted_score
from iperson.core.audit.grounding import check_grounding
from iperson.core.audit.keyword_check import check_keyword_fit
from iperson.core.audit.platform_rules import check_platform_rules
from iperson.core.audit.report import AuditReport, build_audit_json, format_audit_report
from iperson.core.audit.structure_check import check_structure

GOOD_CONTENT = """# RAG技术入门

RAG（检索增强生成）是当前AI领域的热门技术。

## 核心原理

RAG通过结合检索和生成，显著提升了问答系统的准确性。

## 实践步骤

1. 搭建知识库
2. 配置向量检索
3. 接入大模型

## 总结

RAG技术值得每一个AI从业者学习。"""


# =============================================================================
# AuditReport (unchanged from original)
# =============================================================================


class TestAuditReport:
    """Tests for the AuditReport data model."""

    def test_add_dimension(self) -> None:
        """Adding a dimension stores its score and result."""
        report = AuditReport(content_id="test-001")
        report.add_dimension("grounding", {"score": 0.85, "status": "pass"})

        assert report.scores["grounding"] == 0.85
        assert report.dimensions["grounding"]["status"] == "pass"

    def test_overall_status_pass(self) -> None:
        """All scores >= 0.5 and critical >= 0.3 yields pass."""
        report = AuditReport(content_id="test-002")
        report.add_dimension("grounding", {"score": 0.9, "status": "pass"})
        report.add_dimension("keyword_fit", {"score": 0.8, "status": "pass"})
        report.add_dimension("structure", {"score": 0.85, "status": "pass"})

        assert report.overall_status == "pass"

    def test_overall_status_fail_critical(self) -> None:
        """Critical dimension below 0.3 yields fail."""
        report = AuditReport(content_id="test-003")
        report.add_dimension("grounding", {"score": 0.1, "status": "fail"})
        report.add_dimension("keyword_fit", {"score": 0.7, "status": "pass"})

        assert report.overall_status == "fail"

    def test_overall_status_review(self) -> None:
        """Some scores below 0.5 but critical OK yields review."""
        report = AuditReport(content_id="test-004")
        report.add_dimension("grounding", {"score": 0.6, "status": "review"})
        report.add_dimension("keyword_fit", {"score": 0.4, "status": "review"})
        report.add_dimension("structure", {"score": 0.3, "status": "review"})

        assert report.overall_status == "review"

    def test_overall_status_no_scores(self) -> None:
        """No scores yields fail."""
        report = AuditReport(content_id="test-005")
        assert report.overall_status == "fail"

    def test_to_dict(self) -> None:
        """to_dict returns serializable dict with expected keys."""
        report = AuditReport(content_id="test-006")
        report.add_dimension("grounding", {"score": 0.9, "status": "pass"})
        d = report.to_dict()

        assert d["content_id"] == "test-006"
        assert d["overall_status"] == "pass"
        assert "id" in d
        assert "version" in d
        assert "scores" in d
        assert "dimensions" in d
        assert d["scores"]["grounding"] == 0.9


# =============================================================================
# Grounding
# =============================================================================


class TestGrounding:
    """Tests for check_grounding()."""

    def test_grounding_with_kb(self) -> None:
        """Content referencing KB chunks returns score > 0."""
        content = "RAG是检索增强生成技术。它提升了问答系统的准确性。"
        kb_chunks = [
            {"content": "RAG（检索增强生成）是当前AI领域的热门技术。"},
            {"content": "RAG通过结合检索和生成，显著提升了问答系统的准确性。"},
        ]
        result = check_grounding(content, kb_chunks)

        assert result["score"] > 0
        assert result["claims_checked"] > 0
        assert result["verified"] > 0

    def test_grounding_no_kb(self) -> None:
        """No KB chunks returns status 'no_kb' and score 0.5."""
        result = check_grounding("RAG技术入门。", [])

        assert result["status"] == "no_kb"
        assert result["score"] == 0.5
        assert result["claims_checked"] == 0

    def test_grounding_no_match(self) -> None:
        """Content unrelated to KB returns low score."""
        content = "1234567890. abcdefghijklmn."
        kb_chunks = [
            {"content": "RAG（检索增强生成）是AI领域的技术。"},
        ]
        result = check_grounding(content, kb_chunks)

        assert result["score"] < 0.3
        assert result["status"] == "fail"


# =============================================================================
# Keyword Check (new sub-scores API)
# =============================================================================


class TestKeywordCheck:
    """Tests for check_keyword_fit() with sub-scores and suggestions."""

    def test_clean_content_high_score(self) -> None:
        """Content without banned or sensitive words yields high score."""
        content = "这是一个干净的测试文本，不包含任何问题词汇。"
        result = check_keyword_fit(content)

        assert result["score"] == 1.0
        assert result["sub_scores"]["banned_word_ratio"] == 1.0
        assert result["sub_scores"]["sensitive_word_ratio"] == 1.0
        assert result["suggestions"] == []

    def test_banned_words_lower_score(self) -> None:
        """Content with banned words yields score < 1.0."""
        content = "总的来说，这是一个测试。首先，我们要明确目标。"
        result = check_keyword_fit(content)

        assert result["score"] < 1.0
        assert result["sub_scores"]["banned_word_ratio"] < 1.0
        assert "禁用词" in result["suggestions"][0]

    def test_sensitive_words_lower_score(self) -> None:
        """Content with sensitive words yields score < 1.0."""
        content = "这是绝对最好的产品，一定是你的第一选择。"
        result = check_keyword_fit(content)

        assert result["score"] < 1.0
        assert result["sub_scores"]["sensitive_word_ratio"] < 1.0
        assert "敏感词" in result["suggestions"][0]

    def test_sub_scores_and_suggestions_keys(self) -> None:
        """Result always contains sub_scores, suggestions, and details keys."""
        result = check_keyword_fit("普通文本内容。")

        assert "sub_scores" in result
        assert "suggestions" in result
        assert "details" in result
        assert "banned_found" in result["details"]
        assert "sensitive_found" in result["details"]

    def test_config_override(self) -> None:
        """Config can override banned and sensitive word lists."""
        content = "foo bar baz"
        result = check_keyword_fit(
            content,
            config={
                "banned_words": ["foo"],
                "sensitive_words": ["bar"],
            },
        )

        assert result["score"] < 1.0
        assert result["details"]["banned_found"] == ["foo"]
        assert result["details"]["sensitive_found"] == ["bar"]


# =============================================================================
# Structure Check (new sub-scores API)
# =============================================================================


class TestStructureCheck:
    """Tests for check_structure() with sub-scores."""

    def test_good_structure(self) -> None:
        """Content with H1, headings yields decent score."""
        result = check_structure(GOOD_CONTENT)

        assert result["score"] >= 0.5
        assert result["sub_scores"]["heading_hierarchy"] >= 0.5

    def test_no_headings(self) -> None:
        """Content without headings gets low heading score."""
        content = "这是一段简单的文字，没有任何标题和列表。"
        result = check_structure(content)

        assert result["sub_scores"]["heading_hierarchy"] <= 0.3
        assert "缺少标题" in result["suggestions"][0]

    def test_missing_h1(self) -> None:
        """Content with sub-headings but no H1 is penalized."""
        content = "## Section 1\n\nSome text here.\n\n### Subsection\n\nMore text."
        result = check_structure(content)

        assert result["sub_scores"]["heading_hierarchy"] < 1.0
        assert "一级标题" in result["suggestions"][0]

    def test_full_structure_score(self) -> None:
        """Well-structured content with headings and transitions."""
        content = """# Title

Because this is an example, we need transitions. Therefore we use them here.

## Section

However, we also need variety. For example, this paragraph works.

Furthermore, another paragraph with good length here."""
        result = check_structure(content)

        assert result["score"] > 0.5
        assert "sub_scores" in result
        assert "heading_hierarchy" in result["sub_scores"]
        assert "paragraph_length_distribution" in result["sub_scores"]
        assert "logical_flow_score" in result["sub_scores"]

    def test_flow_score_low(self) -> None:
        """Content without transitions gets low flow score and suggestion."""
        content = "# Title\n\nNo transition words here at all."
        result = check_structure(content)

        if result["sub_scores"]["logical_flow_score"] < 0.5:
            assert any("连贯性" in s for s in result["suggestions"])


# =============================================================================
# Platform Rules
# =============================================================================


class TestPlatformRules:
    """Tests for check_platform_rules()."""

    def test_xiaohongshu_compliant(self) -> None:
        """Content under 1000 chars yields score >= 0.7."""
        content = "小红书短文。" * 20  # well under 1000
        result = check_platform_rules(content, "xiaohongshu")

        assert result["score"] >= 0.7
        assert result["status"] == "pass"
        assert result["char_count"] <= 1000
        assert result["issues"] == []

    def test_xiaohongshu_too_long(self) -> None:
        """Content over 1000 chars yields score < 0.7."""
        content = "超长文章内容。" * 200  # well over 1000
        result = check_platform_rules(content, "xiaohongshu")

        assert result["score"] < 0.7
        assert result["char_count"] > 1000
        assert len(result["issues"]) >= 1

    def test_unknown_platform(self) -> None:
        """No rules for platform yields score 1.0."""
        content = "Some content for an unknown platform."
        result = check_platform_rules(content, "unknown_platform")

        assert result["score"] == 1.0
        assert result["status"] == "pass"
        assert result["max_chars"] is None
        assert result["issues"] == []

    def test_wechat_compliant(self) -> None:
        """Content within WeChat limits yields pass."""
        content = "微信公众号文章。" * 50  # within 200-50000
        result = check_platform_rules(content, "wechat")

        assert result["score"] == 1.0
        assert result["status"] == "pass"

    def test_too_short_for_platform(self) -> None:
        """Content below min_chars yields penality."""
        content = "短"
        result = check_platform_rules(content, "wechat")

        assert result["score"] <= 0.5
        assert len(result["issues"]) >= 1


# =============================================================================
# AuditGate (new weighted scoring API)
# =============================================================================


class TestAuditGate:
    """Tests for the new AuditGate with weighted scoring and suggestions."""

    def _make_dimension_scores(
        self, overrides: dict | None = None
    ) -> dict[str, dict]:
        """Helper to build a default set of dimension scores."""
        base = {
            "keyword_fit": {
                "score": 0.9,
                "sub_scores": {
                    "banned_word_ratio": 0.9,
                    "sensitive_word_ratio": 0.9,
                },
                "suggestions": [],
            },
            "structure": {
                "score": 0.85,
                "sub_scores": {
                    "heading_hierarchy": 0.85,
                    "paragraph_length_distribution": 0.8,
                    "logical_flow_score": 0.9,
                },
                "suggestions": [],
            },
            "platform_rules": {
                "score": 1.0,
                "sub_scores": {},
                "suggestions": [],
            },
            "ai_score": {
                "score": 0.2,
                "sub_scores": {},
                "suggestions": [],
            },
            "style_consistency": {
                "score": 0.9,
                "sub_scores": {},
                "suggestions": [],
            },
            "grounding": {
                "score": 0.8,
                "sub_scores": {},
                "suggestions": [],
            },
        }
        if overrides:
            base.update(overrides)
        return base

    def test_full_audit_pass(self) -> None:
        """Good dimension scores yield pass status."""
        gate = AuditGate()
        dim_scores = self._make_dimension_scores()
        result = gate.evaluate(dim_scores)

        assert result["overall_status"] == "pass"
        assert result["overall_score"] >= 0.7
        assert result["below_min_dimension"] == []

    def test_audit_fail_low_score(self) -> None:
        """Very low dimension scores yield fail status."""
        gate = AuditGate()
        dim_scores = self._make_dimension_scores(
            {
                "keyword_fit": {"score": 0.1, "suggestions": []},
                "structure": {"score": 0.2, "suggestions": []},
                "platform_rules": {"score": 0.3, "suggestions": []},
                "style_consistency": {"score": 0.2, "suggestions": []},
            }
        )
        result = gate.evaluate(dim_scores)

        assert result["overall_status"] == "fail"

    def test_audit_scores_structure(self) -> None:
        """Result has all 6 expected dimension keys."""
        gate = AuditGate()
        dim_scores = self._make_dimension_scores()
        result = gate.evaluate(dim_scores)

        expected_keys = {
            "grounding",
            "keyword_fit",
            "structure",
            "platform_rules",
            "style_consistency",
            "ai_score",
        }
        assert expected_keys.issubset(result["scores"].keys())

    def test_audit_empty_scores(self) -> None:
        """Empty dimension scores yields fail."""
        gate = AuditGate()
        result = gate.evaluate({})

        assert result["overall_status"] == "fail"
        assert result["overall_score"] == 0.0

    def test_sub_scores_in_result(self) -> None:
        """Sub-scores from each dimension appear in the result."""
        gate = AuditGate()
        dim_scores = self._make_dimension_scores()
        result = gate.evaluate(dim_scores)

        assert "sub_scores" in result
        assert "keyword_fit" in result["sub_scores"]
        assert "structure" in result["sub_scores"]
        assert "banned_word_ratio" in result["sub_scores"]["keyword_fit"]
        assert "heading_hierarchy" in result["sub_scores"]["structure"]

    def test_suggestions_collected(self) -> None:
        """Suggestions from all dimensions are collected."""
        gate = AuditGate()
        dim_scores = self._make_dimension_scores(
            {
                "keyword_fit": {
                    "score": 0.5,
                    "suggestions": ["禁用词使用: 总的来说"],
                },
                "structure": {
                    "score": 0.3,
                    "suggestions": ["缺少标题", "段落过长"],
                },
            }
        )
        result = gate.evaluate(dim_scores)

        assert len(result["suggestions"]) == 3
        assert "禁用词使用: 总的来说" in result["suggestions"]
        assert "缺少标题" in result["suggestions"]


# =============================================================================
# AuditGate: weighted scoring
# =============================================================================


class TestWeightedScoring:
    """Tests for compute_weighted_score and AuditGate weights."""

    def test_default_weights_equal(self) -> None:
        """Default weights treat all dimensions equally."""
        scores = {"a": 1.0, "b": 0.0}
        result = compute_weighted_score(scores)
        assert result == 0.5

    def test_custom_weights(self) -> None:
        """Custom weights bias the overall score."""
        gate = AuditGate({"weights": {"keyword_fit": 2.0, "structure": 1.0}})
        dim_scores = {
            "keyword_fit": {"score": 0.8, "sub_scores": {}, "suggestions": []},
            "structure": {"score": 0.6, "sub_scores": {}, "suggestions": []},
        }
        result = gate.evaluate(dim_scores)
        # (0.8*2 + 0.6*1) / 3 = 2.2 / 3 = 0.733...
        assert abs(result["overall_score"] - 0.733) < 0.01

    def test_min_dimension_score_blocks(self) -> None:
        """Dimensions below min_dimension_score appear in below_min list."""
        gate = AuditGate({"min_dimension_score": 0.5})
        dim_scores = {
            "keyword_fit": {
                "score": 0.9,
                "sub_scores": {},
                "suggestions": [],
            },
            "structure": {
                "score": 0.3,
                "sub_scores": {},
                "suggestions": ["缺少标题"],
            },
        }
        result = gate.evaluate(dim_scores)
        assert "structure" in result["below_min_dimension"]

    def test_min_dimension_score_prevents_pass(self) -> None:
        """Below-min dimensions prevent pass even if overall score is high."""
        gate = AuditGate({"min_dimension_score": 0.5})
        dim_scores = {
            "keyword_fit": {"score": 0.9, "sub_scores": {}, "suggestions": []},
            "structure": {"score": 0.3, "sub_scores": {}, "suggestions": []},
        }
        result = gate.evaluate(dim_scores)
        assert result["overall_status"] != "pass"

    def test_zero_weight_dimension_ignored(self) -> None:
        """Dimension with zero weight does not affect score."""
        gate = AuditGate({"weights": {"a": 1.0, "b": 0.0}})
        dim_scores = {
            "a": {"score": 1.0, "sub_scores": {}, "suggestions": []},
            "b": {"score": 0.0, "sub_scores": {}, "suggestions": []},
        }
        result = gate.evaluate(dim_scores)
        assert result["overall_score"] == 1.0


# =============================================================================
# Legacy check_gate
# =============================================================================


class TestLegacyGate:
    """Tests for the backward-compatible check_gate()."""

    def test_check_gate_pass(self) -> None:
        """check_gate returns pass for high scores."""
        result = check_gate({"a": 0.9, "b": 0.8})
        assert result["overall_status"] == "pass"

    def test_check_gate_fail(self) -> None:
        """check_gate returns fail for low scores."""
        result = check_gate({"a": 0.2, "b": 0.1})
        assert result["overall_status"] == "fail"

    def test_check_gate_empty(self) -> None:
        """check_gate handles empty scores gracefully."""
        result = check_gate({})
        assert result["overall_status"] == "fail"


# =============================================================================
# Report formatting
# =============================================================================


class TestReportFormatting:
    """Tests for format_audit_report and build_audit_json."""

    def test_format_audit_report(self) -> None:
        """format_audit_report produces expected text format."""
        gate_result = {
            "overall_score": 0.85,
            "overall_status": "pass",
            "scores": {"keyword_fit": 0.9, "structure": 0.8},
            "sub_scores": {},
            "suggestions": ["建议1", "建议2"],
        }
        text = format_audit_report(gate_result)

        assert "审核报告" in text
        assert "0.85" in text
        assert "pass" in text
        assert "建议1" in text
        assert "建议2" in text
        assert "keyword_fit" in text

    def test_build_audit_json(self) -> None:
        """build_audit_json produces expected JSON-serializable dict."""
        gate_result = {
            "overall_score": 0.75,
            "overall_status": "review",
            "scores": {"keyword_fit": 0.7},
            "sub_scores": {"keyword_fit": {"banned_word_ratio": 0.7}},
            "suggestions": ["改进建议"],
        }
        d = build_audit_json(gate_result)

        assert d["overall_score"] == 0.75
        assert d["overall_status"] == "review"
        assert d["suggestions"] == ["改进建议"]
        assert "generated_at" in d
from __future__ import annotations

from iperson.core.audit.gate import AuditGate
from iperson.core.audit.grounding import check_grounding
from iperson.core.audit.keyword_check import check_keyword_fit
from iperson.core.audit.platform_rules import check_platform_rules
from iperson.core.audit.report import AuditReport
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


class TestKeywordCheck:
    """Tests for check_keyword_fit()."""

    def test_keywords_present(self) -> None:
        """Keywords in title and body yields score >= 0.5."""
        content = "# RAG技术入门\n\nRAG是重要的AI技术。"
        result = check_keyword_fit(content, ["RAG", "技术", "AI"])

        assert result["score"] >= 0.5
        assert result["keyword_in_title"] is True
        assert result["keyword_in_body"] is True

    def test_keywords_missing(self) -> None:
        """Keywords not present yields score < 0.5."""
        content = "# 今天天气不错\n\n适合出去散步。"
        result = check_keyword_fit(content, ["RAG", "知识库", "向量检索"])

        assert result["score"] <= 0.5
        assert result["status"] == "fail"

    def test_empty_keywords(self) -> None:
        """No keywords configured yields score 1.0."""
        content = "任何内容都不需要检查关键词。"
        result = check_keyword_fit(content, [])

        assert result["score"] == 1.0
        assert result["status"] == "pass"

    def test_primary_keywords_subset(self) -> None:
        """Only primary keywords are scored."""
        content = "# RAG技术\n\nRAG是重要的AI技术。"
        result = check_keyword_fit(
            content, ["RAG", "技术", "AI", "extra"], primary_keywords=["RAG", "技术"]
        )

        assert result["score"] == 1.0
        assert result["primary_keywords"] == ["RAG", "技术"]
        assert result["keyword_in_title"] is True


class TestStructureCheck:
    """Tests for check_structure()."""

    def test_good_structure(self) -> None:
        """Content with H1, H2, lists yields score >= 0.5."""
        result = check_structure(GOOD_CONTENT)

        assert result["score"] >= 0.5
        assert result["has_h1"] is True
        assert result["has_h2"] is True
        assert result["has_list"] is True

    def test_short_content(self) -> None:
        """Just text without structure yields score < 0.5."""
        content = "这是一段简单的文字，没有任何标题和列表。"
        result = check_structure(content)

        assert result["score"] <= 0.5
        assert result["has_h1"] is False
        assert result["has_h2"] is False
        assert result["has_list"] is False
        assert result["paragraph_count"] == 1

    def test_full_structure_score(self) -> None:
        """Content with H1, H2, H3, list, and paragraphs yields max score."""
        content = """# Title

## Section

### Subsection

Some paragraph text here.

1. Item one
2. Item two

Another paragraph."""
        result = check_structure(content)

        assert result["has_h1"] is True
        assert result["has_h2"] is True
        assert result["has_h3"] is True
        assert result["has_list"] is True
        assert result["paragraph_count"] >= 3
        assert result["score"] == 1.0


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


class TestAuditGate:
    """Integration tests for the full AuditGate."""

    def test_full_audit_pass(self) -> None:
        """Good content with keywords and KB yields pass or review."""
        gate = AuditGate()
        kb_chunks = [
            {"content": "RAG（检索增强生成）是当前AI领域的热门技术。"},
            {"content": "RAG通过结合检索和生成，显著提升了问答系统的准确性。"},
            {"content": "搭建知识库、配置向量检索、接入大模型是RAG实践的关键步骤。"},
        ]

        result = gate.evaluate(
            content=GOOD_CONTENT,
            keywords=["RAG", "检索增强生成", "知识库", "向量检索", "大模型"],
            platform="xiaohongshu",
            kb_chunks=kb_chunks,
            style_score=0.9,
        )

        assert result["overall_status"] in ("pass", "review")
        assert result["scores"]["grounding"] > 0
        assert result["scores"]["keyword_fit"] > 0

    def test_audit_empty_content(self) -> None:
        """Empty content fails the audit."""
        gate = AuditGate()
        result = gate.evaluate(
            content="",
            keywords=["RAG"],
            platform="xiaohongshu",
        )

        assert result["overall_status"] == "fail"

    def test_audit_scores_structure(self) -> None:
        """Result has all 6 expected dimension keys."""
        gate = AuditGate()
        result = gate.evaluate(
            content=GOOD_CONTENT,
            keywords=["RAG"],
            platform="xiaohongshu",
            kb_chunks=[{"content": "RAG技术"}],
            style_score=0.8,
        )

        expected_keys = {
            "grounding",
            "keyword_fit",
            "structure",
            "platform_rules",
            "style_consistency",
            "ai_score",
        }
        assert expected_keys.issubset(result["scores"].keys())

    def test_audit_with_ai_score_passed(self) -> None:
        """Pre-computed ai_score is used correctly."""
        gate = AuditGate()
        result = gate.evaluate(
            content=GOOD_CONTENT,
            keywords=["RAG"],
            platform="xiaohongshu",
            ai_score=0.15,  # low AI-ness = good
        )

        assert result["scores"]["ai_score"] == 0.15

    def test_audit_with_high_ai_score(self) -> None:
        """High AI-ness is flagged appropriately."""
        gate = AuditGate()
        result = gate.evaluate(
            content="值得注意的是，总的来说，首先，其次，最后。",
            keywords=[],
            platform="xiaohongshu",
        )

        assert result["scores"]["ai_score"] > 0.3
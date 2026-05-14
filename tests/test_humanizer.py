from __future__ import annotations

from iperson.core.humanizer import humanize
from iperson.core.humanizer.detector import detect_ai_patterns
from iperson.core.humanizer.scorer import score_ai_ness
from iperson.core.humanizer.transformer import replace_ai_phrases

AI_TEXT = (
    "值得注意的是，RAG技术具有显著的性能优势。总的来说，"
    "这是一种非常有价值的架构方案。首先，它提高了检索效率。"
    "其次，它降低了延迟。最后，它改善了用户体验。"
)
NATURAL_TEXT = (
    "RAG这个东西真的挺好用的。我用了两个月，最大的感受就是"
    "——终于不用再看那些胡说八道的回答了。"
)


class TestDetector:
    """Tests for detect_ai_patterns()."""

    def test_detect_ai_phrases(self) -> None:
        """Text with AI phrases returns detections."""
        findings = detect_ai_patterns(AI_TEXT)

        # Should detect AI phrases
        ai_phrase_types = [f for f in findings if f["type"] == "ai_phrase"]
        assert len(ai_phrase_types) >= 2

        # Should detect sequential structure
        structure_findings = [f for f in findings if f["type"] == "ai_structure"]
        assert len(structure_findings) >= 1

        # Verify specific phrases are found
        phrase_texts = {f["phrase"] for f in ai_phrase_types}
        assert "值得注意的是" in phrase_texts
        assert "总的来说" in phrase_texts

    def test_detect_natural_text(self) -> None:
        """Natural text without AI phrases returns empty list or very few results."""
        findings = detect_ai_patterns(NATURAL_TEXT)

        # Natural text should not have AI phrase detections
        ai_phrase_types = [f for f in findings if f["type"] == "ai_phrase"]
        assert len(ai_phrase_types) == 0

    def test_detect_uniform_structure(self) -> None:
        """Paragraphs with very similar lengths are flagged as uniform."""
        uniform_text = (
            "这是第一段文字内容，长度适中。\n"
            "这是第二段文字内容，长度相当。\n"
            "这是第三段文字内容，长度接近。\n"
            "这是第四段文字内容，长度类似。"
        )
        findings = detect_ai_patterns(uniform_text)

        uniform_findings = [f for f in findings if f["type"] == "uniform_structure"]
        assert len(uniform_findings) >= 1

    def test_detect_empty_text(self) -> None:
        """Empty string returns an empty list."""
        findings = detect_ai_patterns("")
        assert findings == []


class TestTransformer:
    """Tests for replace_ai_phrases()."""

    def test_replace_ai_phrases(self) -> None:
        """'值得注意的是' gets replaced."""
        text = "值得注意的是，这个功能非常强大。"
        result = replace_ai_phrases(text)

        assert "值得注意的是" not in result["text"]
        assert len(result["changes"]) >= 1
        assert result["changes"][0]["from"] == "值得注意的是，"
        assert result["changes"][0]["to"] == "其实"
        assert result["changes"][0]["count"] == 1

    def test_replace_ai_phrases_multiple(self) -> None:
        """Multiple different AI phrases are all replaced."""
        result = replace_ai_phrases(AI_TEXT)

        assert "值得注意的是" not in result["text"]
        assert "总的来说" not in result["text"]
        assert "首先，" not in result["text"]
        assert "其次，" not in result["text"]
        assert "最后，" not in result["text"]
        assert len(result["changes"]) >= 4

    def test_replace_no_changes(self) -> None:
        """Natural text is unchanged."""
        result = replace_ai_phrases(NATURAL_TEXT)

        assert result["text"] == NATURAL_TEXT
        assert result["changes"] == []

    def test_replace_empty_text(self) -> None:
        """Empty text returns no changes."""
        result = replace_ai_phrases("")

        assert result["text"] == ""
        assert result["changes"] == []


class TestScorer:
    """Tests for score_ai_ness()."""

    def test_ai_text_scores_high(self) -> None:
        """AI-laden text scores > 0.3."""
        score = score_ai_ness(AI_TEXT)

        assert score > 0.3
        assert score <= 1.0

    def test_natural_text_scores_low(self) -> None:
        """Natural text scores < 0.3."""
        score = score_ai_ness(NATURAL_TEXT)

        assert score < 0.3
        assert score >= 0.0

    def test_empty_text_scores_zero(self) -> None:
        """Empty text scores 0.0."""
        score = score_ai_ness("")

        assert score == 0.0


class TestHumanizer:
    """Integration tests for the humanize() pipeline."""

    async def test_humanize_pipeline(self) -> None:
        """Run full pipeline, verify score drops and changes are made."""
        result = await humanize(AI_TEXT)

        assert result["text"] != AI_TEXT
        assert len(result["changes"]) > 0
        assert result["score"] >= 0.0
        assert result["iterations"] >= 1

        # Verify the score dropped compared to the original
        original_score = score_ai_ness(AI_TEXT)
        assert result["score"] < original_score

    async def test_humanize_no_changes_needed(self) -> None:
        """Natural text is unchanged by the pipeline."""
        result = await humanize(NATURAL_TEXT)

        assert result["text"] == NATURAL_TEXT
        assert result["changes"] == []
        assert result["score"] < 0.35
        assert result["iterations"] == 0

    async def test_humanize_empty_text(self) -> None:
        """Empty text handled gracefully."""
        result = await humanize("")

        assert result["text"] == ""
        assert result["changes"] == []
        assert result["score"] == 0.0
        assert result["iterations"] == 0

    async def test_humanize_min_score_zero(self) -> None:
        """With min_score=0, pipeline runs all iterations."""
        result = await humanize(AI_TEXT, min_score=0.0)

        # Should have run max_iterations (default 2) times
        assert result["iterations"] == 2
        assert len(result["changes"]) > 0
        # Score should be 0 since min_score=0 forces all iterations
        assert result["score"] >= 0.0

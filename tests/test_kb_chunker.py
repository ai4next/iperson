from __future__ import annotations

import pytest

from iperson.core.kb.chunker import FixedSizeChunker, SemanticChunker


class TestSemanticChunker:
    """Tests for SemanticChunker."""

    def test_splits_at_paragraphs(self) -> None:
        """Multi-paragraph text should produce >= 2 chunks."""
        text = "First paragraph about Python.\n\nSecond paragraph about features.\n\nThird paragraph about use cases."
        chunker = SemanticChunker(chunk_size=512, overlap=64)
        chunks = chunker.chunk(text)
        assert len(chunks) >= 2
        assert all("text" in c and "index" in c for c in chunks)
        assert chunks[0]["index"] == 0
        assert chunks[1]["index"] == 1

    def test_single_short_text(self) -> None:
        """Single short text should produce exactly 1 chunk."""
        text = "Short text."
        chunker = SemanticChunker(chunk_size=512, overlap=64)
        chunks = chunker.chunk(text)
        assert len(chunks) == 1
        assert chunks[0]["text"] == "Short text."
        assert chunks[0]["index"] == 0

    def test_empty_text(self) -> None:
        """Empty text should produce an empty result."""
        chunker = SemanticChunker(chunk_size=512, overlap=64)
        chunks = chunker.chunk("")
        assert chunks == []

    def test_skip_empty_paragraphs(self) -> None:
        """Empty paragraphs should be skipped."""
        text = "Para one.\n\n\n\nPara two."
        chunker = SemanticChunker(chunk_size=512, overlap=0)
        chunks = chunker.chunk(text)
        assert len(chunks) == 2
        assert chunks[0]["text"] == "Para one."
        assert chunks[1]["text"] == "Para two."

    def test_overlap_included(self) -> None:
        """Overlap from previous chunk should be included."""
        text = "A" * 100 + "\n\n" + "B" * 100 + "\n\n" + "C" * 100
        chunker = SemanticChunker(chunk_size=50, overlap=20)
        chunks = chunker.chunk(text)
        assert len(chunks) >= 2
        # Each chunk after the first should include overlap from previous
        for i in range(1, len(chunks)):
            assert len(chunks[i]["text"]) > 0


class TestFixedSizeChunker:
    """Tests for FixedSizeChunker."""

    def test_splits_by_fixed_size(self) -> None:
        """25 chars with chunk_size=10 should produce 3 chunks."""
        text = "ABCDEFGHIJKLMNOPQRSTUVWXY"  # 25 chars
        chunker = FixedSizeChunker(chunk_size=10, overlap=0)
        chunks = chunker.chunk(text)
        assert len(chunks) == 3
        assert chunks[0]["text"] == "ABCDEFGHIJ"
        assert chunks[1]["text"] == "KLMNOPQRST"
        assert chunks[2]["text"] == "UVWXY"
        assert all(c["index"] == i for i, c in enumerate(chunks))

    def test_empty_text(self) -> None:
        """Empty text should produce an empty result."""
        chunker = FixedSizeChunker(chunk_size=10, overlap=0)
        chunks = chunker.chunk("")
        assert chunks == []

    def test_overlap(self) -> None:
        """Overlap should carry content from previous chunk."""
        text = "ABCDEFGHIJKLMNOPQRSTUVWXY"  # 25 chars
        chunker = FixedSizeChunker(chunk_size=10, overlap=3)
        chunks = chunker.chunk(text)
        assert len(chunks) == 3
        # Second chunk should start with last 3 chars of first chunk
        assert chunks[1]["text"].startswith("HIJ")
        # Third chunk should start with last 3 chars of second chunk
        assert chunks[2]["text"].startswith("RST")

    def test_text_shorter_than_chunk_size(self) -> None:
        """Text shorter than chunk_size should produce 1 chunk."""
        text = "Short"
        chunker = FixedSizeChunker(chunk_size=100, overlap=0)
        chunks = chunker.chunk(text)
        assert len(chunks) == 1
        assert chunks[0]["text"] == "Short"
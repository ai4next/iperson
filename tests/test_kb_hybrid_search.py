from __future__ import annotations

import pytest

from iperson.core.kb.bm25 import BM25Index
from iperson.core.kb.context import assemble_context


class TestBM25Index:
    """Tests for BM25Index."""

    def test_index_and_search(self) -> None:
        """Add docs, search, verify relevant result ranked first."""
        index = BM25Index()
        docs = [
            {"id": "1", "text": "Python is a programming language for web development and data science."},
            {"id": "2", "text": "JavaScript is used for frontend web development and interactive websites."},
            {"id": "3", "text": "Rust is a systems programming language focused on safety and performance."},
        ]
        index.add_documents(docs)
        results = index.search("programming language", top_k=5)
        assert len(results) >= 2
        # Python and Rust docs both contain "programming language"
        assert results[0]["id"] in ("1", "3")

    def test_search_empty_index(self) -> None:
        """Empty index returns []."""
        index = BM25Index()
        assert index.search("anything") == []

    def test_search_no_match(self) -> None:
        """Query with no match returns []."""
        index = BM25Index()
        index.add_documents([{"id": "1", "text": "Python programming language."}])
        results = index.search("quantum physics", top_k=5)
        assert results == []

    def test_add_document(self) -> None:
        """Single doc add and search."""
        index = BM25Index()
        index.add_document({"id": "42", "text": "Machine learning is a subset of artificial intelligence."})
        results = index.search("machine learning", top_k=5)
        assert len(results) == 1
        assert results[0]["id"] == "42"
        assert isinstance(results[0]["score"], float)

    def test_clear(self) -> None:
        """After clear, search returns []."""
        index = BM25Index()
        index.add_documents([{"id": "1", "text": "Some text here."}])
        index.clear()
        assert index.size == 0
        assert index.search("text") == []


class TestContextAssembly:
    """Tests for context assembly."""

    def test_assemble(self) -> None:
        """Multi-chunk, verify [Source 1], [Source 2] format."""
        chunks = [
            {"text": "First chunk content.", "metadata": {"id": "1"}},
            {"text": "Second chunk content.", "metadata": {"id": "2"}},
            {"text": "Third chunk content.", "metadata": {"id": "3"}},
        ]
        result = assemble_context(chunks)
        assert "[Source 1]" in result
        assert "[Source 2]" in result
        assert "[Source 3]" in result
        assert "First chunk content." in result
        assert "Second chunk content." in result
        assert result.index("[Source 1]") < result.index("First chunk content.")
        assert result.index("[Source 2]") < result.index("Second chunk content.")

    def test_assemble_empty(self) -> None:
        """Empty chunks."""
        assert assemble_context([]) == ""

    def test_assemble_with_heading(self) -> None:
        """Chunks with heading metadata."""
        chunks = [
            {"text": "Content about Python.", "metadata": {"id": "1", "heading": "Introduction"}},
            {"text": "Content about features.", "metadata": {"id": "2", "heading": "Key Features"}},
        ]
        result = assemble_context(chunks)
        assert "Introduction" in result
        assert "Key Features" in result
        assert "[Source 1]" in result
        assert "Content about Python." in result
        # Heading should appear in the formatted output
        assert "Introduction" in result

    def test_assemble_single(self) -> None:
        """Single chunk."""
        chunks = [
            {"text": "Only chunk.", "metadata": {"id": "1"}},
        ]
        result = assemble_context(chunks)
        assert result == "[Source 1]\nOnly chunk."
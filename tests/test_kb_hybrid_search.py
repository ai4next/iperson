from __future__ import annotations

import numpy as np
import pytest

from iperson.core.kb.bm25 import BM25Index
from iperson.core.kb.context import assemble_context
from iperson.core.kb.hybrid_search import HybridSearch, rrf_merge
from iperson.core.kb.vector_store import VectorStore


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


class TestVectorStore:
    """Tests for VectorStore."""

    def test_search(self) -> None:
        """Add vectors, search, verify results sorted by similarity."""
        store = VectorStore()
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        v3 = [0.9, 0.1, 0.0]
        store.add(v1, {"id": "1", "text": "doc1"})
        store.add(v2, {"id": "2", "text": "doc2"})
        store.add(v3, {"id": "3", "text": "doc3"})

        results = store.search([1.0, 0.0, 0.0], top_k=3)
        assert len(results) == 3
        assert results[0]["id"] == "1"  # most similar
        assert results[1]["id"] == "3"  # second most similar
        assert results[2]["id"] == "2"  # least similar
        assert all(isinstance(r["score"], float) for r in results)
        assert results[0]["score"] >= results[1]["score"] >= results[2]["score"]

    def test_search_empty(self) -> None:
        """Empty store returns []."""
        store = VectorStore()
        assert store.search([1.0, 0.0, 0.0]) == []

    def test_add_batch(self) -> None:
        """Batch add works."""
        store = VectorStore()
        vectors = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
        metadata_list = [{"id": "1"}, {"id": "2"}]
        store.add_batch(vectors, metadata_list)
        assert store.size == 2
        results = store.search([1.0, 0.0, 0.0], top_k=2)
        assert len(results) == 2

    def test_save_load(self, tmp_path: pytest.TempPathFactory) -> None:
        """Save to tmp file, load in new store, verify same results."""
        store = VectorStore()
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        store.add(v1, {"id": "1"})
        store.add(v2, {"id": "2"})

        index_path = tmp_path / "vectors.json"
        store.index_path = str(index_path)
        store.save()

        new_store = VectorStore(index_path=str(index_path))
        new_store.load()
        assert new_store.size == 2
        results = new_store.search([1.0, 0.0, 0.0], top_k=2)
        assert len(results) == 2
        assert results[0]["id"] == "1"

    def test_clear(self) -> None:
        """After clear, size is 0."""
        store = VectorStore()
        store.add([1.0, 0.0, 0.0], {"id": "1"})
        store.clear()
        assert store.size == 0
        assert store.search([1.0, 0.0, 0.0]) == []


class TestHybridSearch:
    """Tests for HybridSearch and rrf_merge."""

    def test_rrf_merge(self) -> None:
        """Merge vector and keyword results, verify ordering."""
        vector_results = [
            {"id": "1", "score": 0.9},
            {"id": "2", "score": 0.8},
            {"id": "3", "score": 0.7},
        ]
        keyword_results = [
            {"id": "2", "score": 0.85},
            {"id": "3", "score": 0.75},
            {"id": "4", "score": 0.6},
        ]
        merged = rrf_merge(vector_results, keyword_results, k=60)
        # All unique IDs present
        ids = {r["id"] for r in merged}
        assert ids == {"1", "2", "3", "4"}
        # Results sorted by RRF score descending
        assert len(merged) == 4
        assert all(isinstance(r["score"], float) for r in merged)
        # ID 2 appears in both lists so should have highest RRF score
        assert merged[0]["id"] == "2"

    def test_rrf_merge_empty(self) -> None:
        """Empty inputs."""
        assert rrf_merge([], [], k=60) == []
        result = rrf_merge([{"id": "1", "score": 0.9}], [], k=60)
        assert len(result) == 1
        assert result[0]["id"] == "1"
        assert result[0]["score"] == pytest.approx(1.0 / 61.0)
        result2 = rrf_merge([], [{"id": "1", "score": 0.9}], k=60)
        assert len(result2) == 1
        assert result2[0]["id"] == "1"
        assert result2[0]["score"] == pytest.approx(1.0 / 61.0)

    def test_rrf_merge_no_overlap(self) -> None:
        """Results with no overlapping IDs."""
        vector_results = [
            {"id": "1", "score": 0.9},
            {"id": "2", "score": 0.8},
        ]
        keyword_results = [
            {"id": "3", "score": 0.85},
            {"id": "4", "score": 0.75},
        ]
        merged = rrf_merge(vector_results, keyword_results, k=60)
        assert len(merged) == 4
        ids = {r["id"] for r in merged}
        assert ids == {"1", "2", "3", "4"}

    async def test_search_hybrid(self) -> None:
        """End-to-end with a VectorStore + BM25Index."""
        import hashlib

        import numpy as np

        vector_store = VectorStore()
        bm25_index = BM25Index()

        docs = [
            {"id": "1", "text": "Python is a programming language for web development."},
            {"id": "2", "text": "JavaScript is used for frontend web development."},
            {"id": "3", "text": "Rust is a systems programming language."},
        ]

        # Generate dummy vectors with proper dimensions
        for doc in docs:
            h = hashlib.sha256(doc["text"].encode()).digest()
            rng = np.frombuffer(h, dtype=np.uint8).astype(np.float32)
            rng = (rng / 127.5) - 1.0
            if len(rng) < 4:
                rng = np.tile(rng, 4 // len(rng) + 1)[:4]
            vector_store.add(rng[:4].tolist(), doc)

        bm25_index.add_documents(docs)

        hs = HybridSearch(vector_store=vector_store, bm25_index=bm25_index)

        query_vector = [1.0, 0.0, 0.0, 0.0]
        results = await hs.search(query="programming language", query_vector=query_vector, top_k=5)
        assert len(results) >= 2
        assert all("id" in r and "score" in r for r in results)
        # Results sorted by RRF score descending
        for i in range(len(results) - 1):
            assert results[i]["score"] >= results[i + 1]["score"]


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
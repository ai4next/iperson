from __future__ import annotations

from typing import Any

from iperson.core.kb.bm25 import BM25Index
from iperson.core.kb.vector_store import VectorStore


def rrf_merge(
    vector_results: list[dict[str, Any]],
    keyword_results: list[dict[str, Any]],
    k: int = 60,
) -> list[dict[str, Any]]:
    """Merge two ranked result lists using Reciprocal Rank Fusion (RRF).

    Each result list contributes a score of 1 / (k + rank) for each document,
    where rank is 1-based position in the list. Scores are summed per document.

    Args:
        vector_results: Ranked results from vector search with 'id' and 'score' keys.
        keyword_results: Ranked results from keyword search with 'id' and 'score' keys.
        k: The RRF constant (default: 60).

    Returns:
        A merged list of dicts with 'id' and 'score' (RRF score) keys,
        sorted by descending RRF score.
    """
    if not vector_results and not keyword_results:
        return []

    # Accumulate RRF scores per document ID
    rrf_scores: dict[str, float] = {}

    for rank, result in enumerate(vector_results, start=1):
        doc_id = result["id"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    for rank, result in enumerate(keyword_results, start=1):
        doc_id = result["id"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    # Sort by descending RRF score
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

    return [
        {"id": doc_id, "score": rrf_scores[doc_id]}
        for doc_id in sorted_ids
    ]


class HybridSearch:
    """Hybrid search combining vector similarity and keyword search via RRF fusion.

    Args:
        vector_store: A VectorStore instance for dense retrieval.
        bm25_index: A BM25Index instance for keyword retrieval.
    """

    def __init__(self, vector_store: VectorStore, bm25_index: BM25Index) -> None:
        self._vector_store = vector_store
        self._bm25_index = bm25_index

    async def search(
        self,
        query: str,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Perform hybrid search using both vector and keyword methods.

        Runs vector search and keyword search in parallel, then merges
        results using Reciprocal Rank Fusion (RRF).

        Args:
            query: The textual query for keyword search.
            query_vector: The query embedding for vector search.
            top_k: Number of top results from each method (default: 5).

        Returns:
            A merged list of dicts with 'id' and 'score' keys,
            sorted by descending RRF score.
        """
        vector_results = self._vector_store.search(query_vector, top_k=top_k)
        keyword_results = self._bm25_index.search(query, top_k=top_k)

        return rrf_merge(vector_results, keyword_results, k=60)
from __future__ import annotations

from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class BM25Index:
    """TF-IDF based keyword index approximating BM25-style search.

    Uses sklearn's TfidfVectorizer with bigram support for keyword-based
    document retrieval with cosine similarity scoring.

    Documents must have 'id' and 'text' keys.
    """

    def __init__(self) -> None:
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=10000)
        self._documents: list[dict[str, Any]] = []
        self._tfidf_matrix = None
        self._is_fitted = False

    def add_documents(self, docs: list[dict[str, Any]]) -> None:
        """Add multiple documents and refit the TF-IDF index.

        Args:
            docs: A list of dicts, each with 'id' and 'text' keys.
        """
        self._documents.extend(docs)
        self._rebuild_index()

    def add_document(self, doc: dict[str, Any]) -> None:
        """Add a single document and refit the TF-IDF index.

        Args:
            doc: A dict with 'id' and 'text' keys.
        """
        self._documents.append(doc)
        self._rebuild_index()

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search for documents by keyword query using TF-IDF cosine similarity.

        Args:
            query: The keyword query string.
            top_k: Number of top results to return (default: 5).

        Returns:
            A list of dicts with document metadata plus a "score" key,
            sorted by descending similarity. Returns [] if the index is empty
            or the query has no matches.
        """
        if not self._documents or not self._is_fitted:
            return []

        query_vec = self._vectorizer.transform([query])
        if query_vec.nnz == 0:
            # Query has no known terms
            return []

        scores = cosine_similarity(query_vec, self._tfidf_matrix).flatten()
        top_indices = scores.argsort()[::-1][:top_k]

        # Only return results with non-zero score
        results: list[dict[str, Any]] = []
        for idx in top_indices:
            score = float(scores[idx])
            if score <= 0:
                continue
            result = dict(self._documents[idx])
            result["score"] = score
            results.append(result)

        return results

    @property
    def size(self) -> int:
        """Return the number of documents in the index."""
        return len(self._documents)

    def clear(self) -> None:
        """Remove all documents and reset the index."""
        self._documents.clear()
        self._tfidf_matrix = None
        self._is_fitted = False
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=10000)

    def _rebuild_index(self) -> None:
        """Rebuild the TF-IDF matrix from all stored documents."""
        if not self._documents:
            self._tfidf_matrix = None
            self._is_fitted = False
            return

        texts = [doc["text"] for doc in self._documents]
        self._tfidf_matrix = self._vectorizer.fit_transform(texts)
        self._is_fitted = True
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np


class VectorStore:
    """In-memory numpy-based vector store with cosine similarity search.

    Supports adding vectors, searching by cosine similarity, and
    persisting to / loading from a JSON file.

    Args:
        index_path: Optional path to a JSON file for persistence.
    """

    def __init__(self, index_path: str | None = None) -> None:
        self.index_path = index_path
        self._vectors: list[list[float]] = []
        self._metadata: list[dict[str, Any]] = []

    def add(self, vector: list[float], metadata: dict[str, Any]) -> None:
        """Add a single vector with metadata.

        Args:
            vector: The embedding vector as a list of floats.
            metadata: A dictionary of metadata associated with this vector.
        """
        self._vectors.append(vector)
        self._metadata.append(metadata)

    def add_batch(self, vectors: list[list[float]], metadata_list: list[dict[str, Any]]) -> None:
        """Add multiple vectors with their associated metadata.

        Args:
            vectors: A list of embedding vectors.
            metadata_list: A list of metadata dicts, one per vector.
        """
        self._vectors.extend(vectors)
        self._metadata.extend(metadata_list)

    def search(self, query_vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        """Search for the top-k most similar vectors by cosine similarity.

        Args:
            query_vector: The query embedding vector.
            top_k: Number of top results to return (default: 5).

        Returns:
            A list of dicts with keys from metadata plus a "score" key,
            sorted by descending cosine similarity.
        """
        if not self._vectors:
            return []

        vectors_np = np.array(self._vectors, dtype=np.float64)
        query_np = np.array(query_vector, dtype=np.float64)

        # Cosine similarity: dot / (norm(v) * norm(q) + epsilon)
        dots = np.dot(vectors_np, query_np)
        v_norms = np.linalg.norm(vectors_np, axis=1)
        q_norm = np.linalg.norm(query_np)
        similarities = dots / (v_norms * q_norm + 1e-10)

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        results: list[dict[str, Any]] = []
        for idx in top_indices:
            result = dict(self._metadata[idx])
            result["score"] = float(similarities[idx])
            results.append(result)

        return results

    def save(self) -> None:
        """Save the vector store to a JSON file.

        The file contains vectors and metadata in a JSON-serializable format.

        Raises:
            ValueError: If no index_path was configured.
        """
        if not self.index_path:
            msg = "No index_path configured. Set index_path before saving."
            raise ValueError(msg)

        data = {
            "vectors": self._vectors,
            "metadata": self._metadata,
        }
        path = Path(self.index_path)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> None:
        """Load the vector store from a JSON file.

        Raises:
            ValueError: If no index_path was configured.
            FileNotFoundError: If the index file does not exist.
        """
        if not self.index_path:
            msg = "No index_path configured. Set index_path before loading."
            raise ValueError(msg)

        path = Path(self.index_path)
        if not path.exists():
            msg = f"Index file not found: {self.index_path}"
            raise FileNotFoundError(msg)

        data = json.loads(path.read_text(encoding="utf-8"))
        self._vectors = data["vectors"]
        self._metadata = data["metadata"]

    @property
    def size(self) -> int:
        """Return the number of vectors in the store."""
        return len(self._vectors)

    def clear(self) -> None:
        """Remove all vectors and metadata from the store."""
        self._vectors.clear()
        self._metadata.clear()
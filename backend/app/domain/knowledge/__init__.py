"""Knowledge Base & RAG — document ingestion, chunking, hybrid search.

In production this integrates with a vector database (Milvus/Qdrant).
This module provides the domain abstractions and a no-op fallback.
"""

from __future__ import annotations

from typing import Any, Protocol


class ChunkingStrategy(Protocol):
    """Interface for text chunking strategies."""

    def chunk(self, text: str, chunk_size: int = 512, overlap: int = 64) -> list[dict[str, Any]]:
        ...


class SemanticChunker:
    """Recursive text chunker that splits on semantic boundaries."""

    MIN_CHUNK = 100
    MAX_CHUNK = 1024

    def chunk(self, text: str, chunk_size: int = 512, overlap: int = 64) -> list[dict[str, Any]]:
        """Split text into overlapping chunks at paragraph/sentence boundaries."""
        # Simple recursive splitting — production would use embedding-based
        chunks: list[dict[str, Any]] = []
        paragraphs = text.split("\n\n")
        current = ""
        idx = 0

        for para in paragraphs:
            if len(current) + len(para) + 2 <= chunk_size:
                current += "\n\n" + para if current else para
            else:
                if current:
                    chunks.append({"text": current, "index": idx, "start": idx * chunk_size})
                    idx += 1
                # Start new chunk with overlap from previous
                overlap_text = current[-overlap:] if len(current) > overlap else current
                current = overlap_text + "\n\n" + para if overlap_text else para

        if current:
            chunks.append({"text": current, "index": idx, "start": idx * chunk_size})

        return chunks


class KnowledgeBaseService:
    """Service layer for document management and semantic retrieval."""

    def __init__(self, chunker: ChunkingStrategy | None = None) -> None:
        self._chunker = chunker or SemanticChunker()

    def chunk_document(self, text: str, chunk_size: int = 512, overlap: int = 64) -> list[dict[str, Any]]:
        """Ingest a document: split into chunks for embedding."""
        return self._chunker.chunk(text, chunk_size, overlap)

    async def hybrid_search(
        self,
        query: str,
        tenant_id: str,
        persona_id: str | None = None,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Hybrid search: vector similarity + keyword match (RRF fusion).

        This is a stub — production requires a vector DB connection.
        """
        # TODO: implement with pgvector or Milvus:
        # 1. Embed query → vector
        # 2. vector_search(query_vector, tenant_id, persona_id, top_k)
        # 3. keyword_search(query, tenant_id, persona_id, top_k)
        # 4. Reciprocal Rank Fusion
        return []

    async def assembly_context(
        self,
        query: str,
        tenant_id: str,
        persona_id: str | None = None,
    ) -> str:
        """Retrieve relevant chunks and assemble into a context string for LLM."""
        results = await self.hybrid_search(query, tenant_id, persona_id)
        if not results:
            return ""

        context_parts = [f"[Source {i+1}] {r.get('text', '')}" for i, r in enumerate(results)]
        return "\n\n".join(context_parts)
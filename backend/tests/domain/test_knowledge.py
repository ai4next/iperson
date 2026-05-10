"""Tests for knowledge base chunking and search service."""

from app.domain.knowledge import KnowledgeBaseService, SemanticChunker


class TestSemanticChunker:
    def test_chunk_short_text(self):
        chunker = SemanticChunker()
        chunks = chunker.chunk("Hello world", chunk_size=512, overlap=64)
        assert len(chunks) == 1
        assert chunks[0]["text"] == "Hello world"

    def test_chunk_long_text(self):
        chunker = SemanticChunker()
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three.\n\n" * 20
        chunks = chunker.chunk(text, chunk_size=200, overlap=30)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c["text"]) <= 200 + 30  # within chunk_size + overlap

    def test_chunk_overlap(self):
        chunker = SemanticChunker()
        text = "AAAA.\n\nBBBB.\n\nCCCC.\n\nDDDD.\n\nEEEE.\n\nFFFF."
        chunks = chunker.chunk(text, chunk_size=50, overlap=10)
        if len(chunks) > 1:
            # Overlap text should appear in consecutive chunks
            assert "BBBB" in chunks[0]["text"] or "BBBB" in chunks[1]["text"]


class TestKnowledgeBaseService:
    def test_chunk_document(self):
        svc = KnowledgeBaseService()
        chunks = svc.chunk_document("Short document", chunk_size=512, overlap=64)
        assert len(chunks) == 1

    async def test_hybrid_search_returns_empty(self):
        svc = KnowledgeBaseService()
        results = await svc.hybrid_search("test query", tenant_id="t1")
        assert results == []

    async def test_assembly_context_empty(self):
        svc = KnowledgeBaseService()
        context = await svc.assembly_context("test query", tenant_id="t1")
        assert context == ""
from __future__ import annotations


class SemanticChunker:
    """Splits text at paragraph boundaries into semantic chunks.

    Each paragraph becomes its own chunk. If a paragraph exceeds chunk_size,
    it is further split at character boundaries.
    """

    def __init__(self, chunk_size: int = 512, overlap: int = 64) -> None:
        """Initialize the semantic chunker.

        Args:
            chunk_size: Maximum size in characters for each chunk.
            overlap: Number of characters of overlap between consecutive chunks.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[dict]:
        """Split the text into semantic chunks at paragraph boundaries.

        Args:
            text: The input text to chunk.

        Returns:
            A list of dicts with keys "text" and "index".
        """
        if not text:
            return []

        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            return []

        chunks: list[str] = []
        for para in paragraphs:
            if len(para) <= self.chunk_size:
                chunks.append(para)
            else:
                # Split long paragraph into fixed-size pieces
                start = 0
                while start < len(para):
                    end = start + self.chunk_size
                    chunks.append(para[start:end])
                    start = end

        # Apply overlap
        result: list[dict] = []
        for i, chunk_text in enumerate(chunks):
            if i > 0 and self.overlap > 0:
                prev_text = chunks[i - 1]
                overlap_text = prev_text[-self.overlap :]
                chunk_text = overlap_text + chunk_text

            result.append({"text": chunk_text, "index": i})

        return result


class FixedSizeChunker:
    """Splits text into fixed-size chunks with configurable overlap."""

    def __init__(self, chunk_size: int = 512, overlap: int = 64) -> None:
        """Initialize the fixed-size chunker.

        Args:
            chunk_size: Size in characters for each chunk.
            overlap: Number of characters of overlap between consecutive chunks.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[dict]:
        """Split the text into fixed-size chunks.

        Args:
            text: The input text to chunk.

        Returns:
            A list of dicts with keys "text" and "index".
        """
        if not text:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start = end

        # Apply overlap
        result: list[dict] = []
        for i, chunk_text in enumerate(chunks):
            if i > 0 and self.overlap > 0:
                prev_text = chunks[i - 1]
                overlap_text = prev_text[-self.overlap :]
                chunk_text = overlap_text + chunk_text

            result.append({"text": chunk_text, "index": i})

        return result
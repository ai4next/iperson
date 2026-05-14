from __future__ import annotations

from typing import Any


def assemble_context(chunks: list[dict[str, Any]], query: str = "") -> str:
    """Assemble a formatted context string from a list of text chunks.

    Each chunk is formatted as:
        [Source N]
        {text}

    If a chunk has a "heading" in its metadata, it is included as a prefix
    to the text on a separate line.

    Args:
        chunks: A list of dicts, each with "text" and optionally "metadata"
            containing a "heading" key.
        query: An optional query string (currently unused but reserved for
            future use such as query-specific formatting).

    Returns:
        A formatted context string, or an empty string if chunks is empty.
    """
    if not chunks:
        return ""

    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        text = chunk["text"]
        metadata = chunk.get("metadata", {})

        if metadata and "heading" in metadata and metadata["heading"]:
            text = f"{metadata['heading']}\n{text}"

        parts.append(f"[Source {i}]\n{text}")

    return "\n\n".join(parts)
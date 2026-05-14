from __future__ import annotations

import re


def check_grounding(content: str, kb_chunks: list[dict]) -> dict:
    """Verify content claims against knowledge base chunks.

    Splits content into sentences and checks each against the provided KB chunks.
    A claim is considered verified if a significant portion of its text overlaps
    with at least one KB chunk.

    Args:
        content: The text to check.
        kb_chunks: A list of dicts, each with at least a "content" or "text" key.

    Returns:
        A dict with:
            - score: float (0.0-1.0)
            - status: "pass" | "review" | "fail" | "no_kb"
            - claims_checked: int
            - verified: int
            - details: list of claim verification results
    """
    if not kb_chunks:
        return {
            "score": 0.5,
            "status": "no_kb",
            "claims_checked": 0,
            "verified": 0,
            "details": [],
        }

    # Extract KB text for comparison
    kb_texts = []
    for chunk in kb_chunks:
        chunk_text = chunk.get("content") or chunk.get("text", "")
        if chunk_text:
            kb_texts.append(chunk_text)

    # Split content into sentences
    sentences = re.split(r"(?<=[。！？.!?])\s*", content)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]

    total_claims = len(sentences)
    verified_claims = 0
    details: list[dict] = []

    for sentence in sentences:
        # Check if the sentence is supported by any KB chunk
        # Use character overlap as a simple proxy for grounding
        supported = False
        for kb_text in kb_texts:
            # Count shared characters (Chinese chars or alphanumeric tokens)
            sentence_chars = set(sentence)
            kb_chars = set(kb_text)
            overlap = len(sentence_chars & kb_chars)
            if overlap / max(len(sentence_chars), 1) >= 0.15:
                supported = True
                break

        if supported:
            verified_claims += 1

        details.append({
            "claim": sentence[:80],
            "verified": supported,
        })

    score = verified_claims / max(total_claims, 1)
    score = min(score, 1.0)

    if score >= 0.8:
        status = "pass"
    elif score >= 0.3:
        status = "review"
    else:
        status = "fail"

    return {
        "score": score,
        "status": status,
        "claims_checked": total_claims,
        "verified": verified_claims,
        "details": details,
    }
from __future__ import annotations

from typing import Any, TypedDict


class PipelineState(TypedDict, total=False):
    """State passed between LangGraph nodes."""

    # Flow control
    status: str                           # running / completed / error

    # Stage outputs
    kb_chunks: list[dict[str, Any]]       # Research → pre-loaded KB chunks
    kb_context: str                       # Research → knowledge base context
    topic: str                            # Topic Selection → chosen topic
    generated_content: str                # Generate → full article
    platform_contents: dict[str, str]     # Platformize → {platform: adapted_content}
    publish_results: list[dict[str, Any]] # Publish → per-platform publish records

    # Runtime
    errors: list[dict[str, Any]]
    data: dict[str, Any]                  # llm_client, persona_engine, etc.
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContentRecord(BaseModel):
    """Represents a piece of generated content (article, post, etc.)."""

    id: str
    persona_name: str | None = None
    pipeline_name: str | None = None
    topic: str = ""
    title: str = ""
    content_type: str = ""
    draft_content: str | None = None
    final_content: str | None = None
    quality_score: float | None = None
    style_consistency: float | None = None
    ai_score: float | None = None
    model_used: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PublicationRecord(BaseModel):
    """Represents a publication of content to a platform."""

    id: str
    content_id: str
    platform: str
    status: str = "draft"
    published_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class KbDocRecord(BaseModel):
    """Represents a knowledge base document."""

    id: str
    title: str
    source: str = ""
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class KbChunkRecord(BaseModel):
    """Represents a chunk of a knowledge base document."""

    id: str
    kb_doc_id: str
    chunk_index: int
    content: str
    created_at: datetime | None = None
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContentRecord(BaseModel):
    """Represents a piece of generated content (article, post, etc.)."""

    id: str
    persona_id: str | None = None
    recipe_name: str | None = None
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


class PersonaRecord(BaseModel):
    """Represents a persona definition with detailed instruction fields."""

    id: str
    name: str = ""
    persona_type: str = ""
    language: str = "zh-CN"
    system_prompt: str = ""
    tone_instruction: str = ""
    style_profile: str = ""
    few_shot_examples: str = ""
    banned_patterns: str = ""
    keywords: str = ""
    focus_areas: str = ""
    content_types: str = ""
    is_active: int = 1
    config: dict[str, Any] = Field(default_factory=dict)
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
    """Represents a chunk of a knowledge base document with optional embedding."""

    id: str
    kb_doc_id: str
    chunk_index: int
    content: str
    embedding: bytes | None = None
    created_at: datetime | None = None


class AuditReportRecord(BaseModel):
    """Represents an audit report."""

    id: str
    report_type: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class PipelineRunRecord(BaseModel):
    """Represents a pipeline execution run."""

    id: str
    pipeline_name: str
    status: str = "pending"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
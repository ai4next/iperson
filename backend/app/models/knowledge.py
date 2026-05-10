"""Knowledge base — documents and vector chunks for RAG."""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TenantMixin, _uuid


class KnowledgeDoc(Base, TenantMixin):
    __tablename__ = "knowledge_docs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    persona_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("personas.id"), default=None, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50), default="upload"
    )  # article | video_transcript | voice | upload
    source_url: Mapped[str | None] = mapped_column(Text, default=None)
    content_text: Mapped[str | None] = mapped_column(Text, default=None)
    file_path: Mapped[str | None] = mapped_column(Text, default=None)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(type_=String(2048), default=None)


class KnowledgeChunk(Base, TenantMixin):
    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    doc_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("knowledge_docs.id"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(type_=String(2048), default=None)
"""Pipeline domain service — the core content production engine.

Extends IPulse's 6-stage pipeline (Discovery→Ranking→Generation→Adaptation
→Quality→Publishing) to 8 stages by adding Research and Human Review.
Each stage is a self-contained step that transforms PipelineContext.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Protocol


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class PipelineContext:
    """Mutable context flowing through all pipeline stages."""

    tenant_id: str
    persona_id: str
    content_id: str | None = None
    topic_id: str | None = None

    # Stage outputs accumulate here
    topics: list[dict[str, Any]] = field(default_factory=list)
    selected_topic: dict[str, Any] | None = None
    research_results: list[dict[str, Any]] = field(default_factory=list)
    draft_content: str | None = None
    adapted_content: dict[str, str] = field(default_factory=dict)  # platform -> content
    quality_results: list[dict[str, Any]] = field(default_factory=list)
    publish_results: list[dict[str, Any]] = field(default_factory=list)

    # Execution tracking
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)

    def to_snapshot(self) -> dict[str, Any]:
        """Serialize to dict for checkpoint persistence."""
        return {
            "tenant_id": self.tenant_id,
            "persona_id": self.persona_id,
            "content_id": self.content_id,
            "topic_id": self.topic_id,
            "selected_topic": self.selected_topic,
            "draft_content": self.draft_content,
            "adapted_content": self.adapted_content,
            "errors": self.errors,
        }


class StageProtocol(Protocol):
    """Interface each pipeline stage must implement."""

    name: str

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        ...


class PipelineOrchestrator:
    """Sequential stage runner with checkpoint & error handling."""

    def __init__(self, stages: list[StageProtocol]) -> None:
        self.stages = stages

    async def run(self, ctx: PipelineContext) -> PipelineContext:
        ctx.started_at = datetime.now(UTC)

        for stage in self.stages:
            try:
                ctx = await stage.execute(ctx)
            except Exception as exc:
                ctx.errors.append({"stage": stage.name, "error": str(exc), "time": str(datetime.now(UTC))})
                # Continue to next stage — non-fatal by default

        ctx.completed_at = datetime.now(UTC)
        return ctx
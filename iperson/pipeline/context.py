from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


class PipelineContext:
    """Holds all state for a single pipeline run, including stage outputs and timing."""

    def __init__(
        self,
        persona_name: str = "",
        topic: str = "",
        content_id: str | None = None,
    ) -> None:
        self.id: str = uuid.uuid4().hex
        self.persona_name: str = persona_name
        self.topic: str = topic
        self.content_id: str | None = content_id
        self.status: str = "running"

        # Stage outputs
        self.kb_chunks: list[dict[str, Any]] = []
        self.kb_context: str = ""
        self.generated_content: str = ""
        self.publish_results: list[dict[str, Any]] = []
        self.platform_contents: dict[str, str] = {}

        # General-purpose data store
        self.data: dict[str, Any] = {}

        # Timing
        self.started_at: str = datetime.now(timezone.utc).isoformat()
        self.completed_at: str | None = None
        self.errors: list[dict[str, Any]] = []

    def to_snapshot(self) -> dict[str, Any]:
        """Serialize the current context state to a dictionary."""
        return {
            "id": self.id,
            "persona_name": self.persona_name,
            "topic": self.topic,
            "content_id": self.content_id,
            "status": self.status,
            "kb_chunks": deepcopy(self.kb_chunks),
            "kb_context": self.kb_context,
            "generated_content": self.generated_content,
            "publish_results": deepcopy(self.publish_results),
            "platform_contents": deepcopy(self.platform_contents),
            "data": deepcopy(self.data),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "errors": deepcopy(self.errors),
        }

    @classmethod
    def from_snapshot(cls, snapshot: dict[str, Any]) -> PipelineContext:
        """Restore a context from a snapshot dictionary."""
        ctx = cls(
            persona_name=snapshot.get("persona_name", ""),
            topic=snapshot.get("topic", ""),
            content_id=snapshot.get("content_id"),
        )
        ctx.id = snapshot.get("id", ctx.id)
        ctx.status = snapshot.get("status", "running")
        ctx.kb_chunks = deepcopy(snapshot.get("kb_chunks", []))
        ctx.kb_context = snapshot.get("kb_context", "")
        ctx.generated_content = snapshot.get("generated_content", "")
        ctx.publish_results = deepcopy(snapshot.get("publish_results", []))
        ctx.platform_contents = deepcopy(snapshot.get("platform_contents", {}))
        ctx.data = deepcopy(snapshot.get("data", {}))
        ctx.started_at = snapshot.get("started_at", ctx.started_at)
        ctx.completed_at = snapshot.get("completed_at")
        ctx.errors = deepcopy(snapshot.get("errors", []))
        return ctx
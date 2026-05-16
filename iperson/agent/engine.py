from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class AgentRun:
    topic: str
    persona: str
    status: str = "pending"
    content_id: str = ""
    started_at: str = ""
    completed_at: str = ""
    error: str = ""


class DigitalTwinAgent:
    """Autonomous agent that plans, generates, and publishes content without human input."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.default_persona = self.config.get("persona", "default")

    async def run_once(self, topic: str) -> AgentRun:
        """Run a single end-to-end content cycle."""
        from iperson.config import ensure_data_dirs
        from iperson.core.persona.profile import load_persona
        from iperson.pipeline.context import PipelineContext
        from iperson.pipeline.orchestrator import PipelineOrchestrator
        from iperson.pipeline.registry import PluginRegistry
        from iperson.storage import init_db
        from iperson.utils.llm import get_llm

        run = AgentRun(
            topic=topic,
            persona=self.default_persona,
            started_at=datetime.now(timezone.utc).isoformat(),
        )

        try:
            ensure_data_dirs()
            init_db()

            llm_client = get_llm("generation")

            persona_profile = load_persona(self.default_persona)
            pipeline_data = persona_profile.pipeline if persona_profile else {"nodes": []}

            registry = PluginRegistry()
            ctx = PipelineContext(topic=topic)
            ctx.data["llm_client"] = llm_client
            ctx.data["platform"] = self.config.get("platform", "xiaohongshu")

            orchestrator = PipelineOrchestrator(registry)
            result = await orchestrator.run(ctx, pipeline_data)

            run.content_id = result.id
            run.status = result.status
            run.completed_at = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            run.status = "failed"
            run.error = str(e)

        return run

    async def run_autonomous(self, count: int = 1) -> list[AgentRun]:
        """Automatically select topics and generate content."""
        from iperson.topics.engine import TopicSuggestionEngine

        engine = TopicSuggestionEngine()
        suggestions = engine.suggest_all(top_n=count)

        if not suggestions:
            return []

        runs = []
        for suggestion in suggestions:
            run = await self.run_once(suggestion.topic)
            runs.append(run)

        return runs
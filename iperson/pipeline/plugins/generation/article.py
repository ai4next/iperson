from __future__ import annotations

from typing import Any

from iperson.core.generation.engine import GenerationEngine
from iperson.core.persona.profile import PersonaProfile
from iperson.pipeline.context import PipelineContext
from iperson.pipeline.plugin import StagePlugin


class ArticleGenerationPlugin(StagePlugin):
    """Generate article content using a persona and LLM."""

    plugin_id: str = "generation.article"
    name: str = "Article Generator"
    description: str = "Generate article content from persona, topic, and KB context"
    category: str = "generation"
    version: str = "1.0.0"

    async def execute(
        self, ctx: PipelineContext, config: dict[str, Any] | None = None
    ) -> PipelineContext:
        """Generate article content using the GenerationEngine.

        Requires ``ctx.data["llm_client"]`` (a ``BaseChatModel`` instance) and
        ``ctx.data["persona"]`` (a dict of persona fields).

        Sets ``ctx.generated_content`` and ``ctx.data["generation_messages"]``.
        """
        llm = ctx.data.get("llm_client")
        if llm is None:
            ctx.errors.append(
                {
                    "plugin": self.plugin_id,
                    "error": "No llm_client found in context data",
                }
            )
            return ctx

        persona_data = ctx.data.get("persona", {})
        persona = PersonaProfile(**persona_data)

        engine = GenerationEngine(llm)

        topic: dict[str, Any] = {"title": ctx.topic}
        topic_summary = ctx.data.get("topic_summary")
        if topic_summary:
            topic["summary"] = topic_summary

        result = await engine.generate(
            persona, topic, kb_context=ctx.kb_context
        )

        ctx.generated_content = result["content"]
        ctx.data["generation_messages"] = result["messages"]

        return ctx
from __future__ import annotations

from typing import Any

from iperson.core.generation.engine import GenerationEngine
from iperson.core.persona.engine import PersonaEngine
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
        either ``ctx.data["persona_engine"]`` or ``ctx.data["persona"]`` (dict).

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

        # Resolve persona — prefer persona_engine, fall back to persona dict
        persona_engine: PersonaEngine | None = ctx.data.get("persona_engine")
        if persona_engine is None:
            persona_data = ctx.data.get("persona", {})
            persona = PersonaProfile(**persona_data)
            persona_engine = PersonaEngine(persona)

        engine = GenerationEngine(llm)

        topic: dict[str, Any] = {"title": ctx.topic}
        topic_summary = ctx.data.get("topic_summary")
        if topic_summary:
            topic["summary"] = topic_summary

        result = await engine.generate(
            persona_engine.persona, topic, kb_context=ctx.kb_context
        )

        ctx.generated_content = result["content"]
        ctx.data["generation_messages"] = result["messages"]

        return ctx
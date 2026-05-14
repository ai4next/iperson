from __future__ import annotations

from typing import Any

from iperson.core.kb.context import assemble_context
from iperson.pipeline.context import PipelineContext
from iperson.pipeline.plugin import StagePlugin


class KbRetrievePlugin(StagePlugin):
    """Retrieve and assemble knowledge base context from pre-loaded chunks."""

    plugin_id: str = "research.kb_retrieve"
    name: str = "KB Retrieve"
    description: str = "Assemble knowledge base context from pre-loaded chunks"
    category: str = "research"
    version: str = "1.0.0"
    default_config: dict[str, Any] = {"top_k": 5}

    async def execute(
        self, ctx: PipelineContext, config: dict[str, Any] | None = None
    ) -> PipelineContext:
        """Assemble KB context from chunks and set it on the context.

        If ``ctx.kb_chunks`` is empty, ``ctx.kb_context`` is set to an empty
        string and the pipeline continues without KB grounding.
        """
        merged = {**self.default_config, **(config or {})}
        top_k = merged["top_k"]

        chunks = ctx.kb_chunks[:top_k] if ctx.kb_chunks else []
        ctx.kb_context = assemble_context(chunks, query=ctx.topic)
        return ctx
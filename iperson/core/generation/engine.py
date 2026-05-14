from __future__ import annotations

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser

from iperson.core.generation.prompts import build_generation_prompt, get_generation_parser
from iperson.core.output.schemas import GenerationOutput
from iperson.core.persona.profile import PersonaProfile
from iperson.utils.llm import get_llm


class GenerationEngine:
    """Orchestrates content generation by combining persona, topic, and KB context.

    Uses LangChain ``BaseChatModel`` with optional Pydantic output parsing for
    structured generation results.
    """

    def __init__(self, llm: BaseChatModel | None = None, stage: str = "generation") -> None:
        self.llm = llm or get_llm(stage)

    async def generate(
        self,
        persona: PersonaProfile,
        topic: dict[str, Any],
        kb_context: str = "",
        temperature: float | None = None,
        structured: bool = False,
    ) -> dict[str, Any]:
        """Generate content for the given persona and topic.

        Args:
            persona: The persona profile defining the generation voice.
            topic: Dictionary with ``title`` and optionally ``summary``.
            kb_context: Optional knowledge base context for factual grounding.
            temperature: Sampling temperature. Uses the model's default if None.
            structured: If True, returns structured ``GenerationOutput`` instead of raw text.

        Returns:
            A dict with ``content``, ``messages``, and ``topic``.
            When ``structured=True``, also includes ``title`` and ``summary``.
        """
        llm = self.llm.with_config(configurable={"temperature": temperature}) if temperature is not None else self.llm
        prompt = build_generation_prompt(persona, topic, kb_context, structured=structured)

        title = topic.get("title", "")
        summary = topic.get("summary", "")
        input_vars: dict[str, Any] = {"title": title, "summary": summary}

        if structured:
            parser: PydanticOutputParser = get_generation_parser()
            input_vars["format_instructions"] = parser.get_format_instructions()
            messages = prompt.format_messages(**input_vars)
            result = await llm.ainvoke(messages)
            parsed = parser.parse(result.content)
            assert isinstance(parsed, GenerationOutput)
            return {
                "content": parsed.content,
                "title": parsed.title,
                "summary": parsed.summary,
                "messages": [{"role": m.type, "content": m.content} for m in messages],
                "topic": topic,
            }

        messages = prompt.format_messages(**input_vars)
        result = await llm.ainvoke(messages)
        return {
            "content": result.content,
            "messages": [{"role": m.type, "content": m.content} for m in messages],
            "topic": topic,
        }

from __future__ import annotations

from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from iperson.core.output.schemas import GenerationOutput
from iperson.core.persona.engine import PersonaEngine
from iperson.core.persona.profile import PersonaProfile

SYSTEM_TEMPLATE = """{persona_prompt}

## Knowledge Base Context
Use the following information as factual grounding. Reference sources by number.
Do not make claims that contradict the provided sources.

{kb_context}"""

USER_TEMPLATE_ZH = (
    "主题: {title}\n摘要: {summary}\n\n"
    "请根据以上主题撰写一篇内容。要求:\n"
    "- 开头吸引人，有个人观点\n"
    "- 正文结构清晰，论证有力\n"
    "- 结尾有互动引导\n"
    "- 内容控制在200-800字\n"
    "- 不要使用AI套话"
)

USER_TEMPLATE_EN = (
    "Topic: {title}\nSummary: {summary}\n\n"
    "Please write content based on the above topic. Requirements:\n"
    "- Engaging opening with personal perspective\n"
    "- Clear structure with strong arguments\n"
    "- Interactive ending to engage readers\n"
    "- Keep content between 200-800 words\n"
    "- Avoid AI cliches"
)


def build_generation_prompt(
    persona: PersonaProfile,
    topic: dict[str, Any],
    kb_context: str = "",
    structured: bool = False,
) -> ChatPromptTemplate:
    """Build a ``ChatPromptTemplate`` for content generation.

    Args:
        persona: The persona profile defining the voice.
        topic: Dictionary with at least ``title`` and optionally ``summary``.
        kb_context: Optional knowledge base context string.
        structured: If True, include format instructions for structured output.

    Returns:
        A ``ChatPromptTemplate`` ready to chain with an LLM.
    """
    persona_engine = PersonaEngine(persona)
    persona_prompt = persona_engine.build_system_prompt()
    system_content = (
        SYSTEM_TEMPLATE.format(persona_prompt=persona_prompt, kb_context=kb_context)
        if kb_context
        else persona_prompt
    )

    title = topic.get("title", "")
    summary = topic.get("summary", "")
    template_str = USER_TEMPLATE_ZH if persona.language == "zh" else USER_TEMPLATE_EN

    if structured:
        parser = PydanticOutputParser(pydantic_object=GenerationOutput)
        template_str += "\n\n{format_instructions}"
        messages = [("system", system_content), ("human", template_str)]
        return ChatPromptTemplate.from_messages(messages).partial(
            title=title,
            summary=summary,
            format_instructions=parser.get_format_instructions(),
        )

    messages = [("system", system_content), ("human", template_str)]
    return ChatPromptTemplate.from_messages(messages).partial(
        title=title,
        summary=summary,
    )


def get_generation_parser() -> PydanticOutputParser:
    """Get a ``PydanticOutputParser`` for ``GenerationOutput``."""
    return PydanticOutputParser(pydantic_object=GenerationOutput)

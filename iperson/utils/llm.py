from __future__ import annotations

import asyncio
import hashlib
from functools import lru_cache
from typing import Any, TypeVar

from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI

from iperson.config import get_provider_for_stage


@lru_cache(maxsize=32)
def _cached_llm(
    provider: str,
    model: str,
    temperature: float,
    api_key: str = "",
    base_url: str = "",
) -> BaseChatModel:
    """Create and cache an LLM instance keyed by (provider, model, temperature)."""
    key = api_key or None
    url = base_url or None
    if provider == "anthropic":
        return ChatAnthropic(model=model, temperature=temperature, api_key=key, base_url=url, thinking={"type": "disabled"})
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=model, temperature=temperature, api_key=key)
    return ChatOpenAI(model=model, temperature=temperature, api_key=key, base_url=url)


def get_llm(stage: str = "default") -> BaseChatModel:
    """Get a cached LLM instance configured for the given pipeline stage.

    Uses per-stage provider config from ``~/.iperson/config.yaml``,
    falling back to the ``default`` stage, then to the top-level ``llm`` config.
    """
    cfg = get_provider_for_stage(stage)
    return _cached_llm(
        provider=cfg.provider,
        model=cfg.model,
        temperature=cfg.temperature,
        api_key=cfg.api_key or "",
        base_url=cfg.base_url or "",
    )


def clear_llm_cache() -> None:
    """Clear all cached LLM instances."""
    _cached_llm.cache_clear()


T = TypeVar("T")


async def retry_llm(factory, retries: int = 2) -> T:
    """Retry an async LLM call with exponential backoff.

    Usage::

        result = await retry_llm(lambda: llm.ainvoke(messages))
    """
    for attempt in range(retries + 1):
        try:
            return await factory()
        except Exception:
            if attempt < retries:
                await asyncio.sleep(2**attempt)
            else:
                raise


# ── Dummy LLM for testing ─────────────────────────────────────────────────


class DummyLLM(BaseChatModel):
    """A fake LangChain chat model that returns deterministic outputs for testing.

    Usage::

        llm = DummyLLM(response="fixed content")
        result = await llm.ainvoke([HumanMessage(content="hello")])
        assert result.content == "fixed content"
    """

    response: str | None = None
    """Fixed response string. If None, a hash-based response is generated."""
    temperature: float = 0.7

    def __init__(self, response: str | None = None, **kwargs: Any) -> None:
        kwargs.setdefault("temperature", 0.7)
        super().__init__(response=response, **kwargs)  # type: ignore[arg-type]

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=self._get_content(messages)))]
        )

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        return self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)

    @property
    def _llm_type(self) -> str:
        return "dummy"

    def _get_content(self, messages: list[BaseMessage]) -> str:
        if self.response is not None:
            return self.response
        combined = " ".join(m.content if isinstance(m.content, str) else "" for m in messages)
        h = hashlib.sha256(combined.encode()).hexdigest()[:32]
        return f"Dummy response for hash: {h}"

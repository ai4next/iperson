from __future__ import annotations

import asyncio
import hashlib
from functools import lru_cache
from typing import Any, TypeVar

import numpy as np
from langchain_anthropic import ChatAnthropic
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

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


@lru_cache(maxsize=4)
def get_embedding(
    model: str = "text-embedding-3-small",
    api_key: str = "",
) -> OpenAIEmbeddings:
    """Get a cached OpenAI embeddings instance."""
    from iperson.config import load_config

    cfg = load_config()
    llm_cfg = cfg.get("llm", {})
    key = api_key or (isinstance(llm_cfg, dict) and llm_cfg.get("api_key", "")) or None
    return OpenAIEmbeddings(model=model, api_key=key)


def clear_llm_cache() -> None:
    """Clear all cached LLM and embedding instances."""
    _cached_llm.cache_clear()
    get_embedding.cache_clear()


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


class DummyEmbeddings:
    """A fake embedder that returns deterministic vectors for testing."""

    def __init__(self, dimension: int = 1536) -> None:
        self.dimension = dimension

    def embed_query(self, text: str) -> list[float]:
        return self._make_vector(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._make_vector(t) for t in texts]

    async def aembed_query(self, text: str) -> list[float]:
        return self._make_vector(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._make_vector(t) for t in texts]

    def _make_vector(self, text: str) -> list[float]:
        if not text.strip():
            return [0.0] * self.dimension
        h = hashlib.sha256(text.encode()).digest()
        rng = np.frombuffer(h, dtype=np.uint8).astype(np.float32)
        rng = (rng / 127.5) - 1.0
        if len(rng) < self.dimension:
            rng = np.tile(rng, self.dimension // len(rng) + 1)[:self.dimension]
        return rng[:self.dimension].tolist()

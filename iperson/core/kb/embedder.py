from __future__ import annotations

from typing import Protocol

from langchain_openai import OpenAIEmbeddings

from iperson.utils.llm import get_embedding


class Embedder(Protocol):
    """Protocol for text embedding implementations."""

    async def embed(self, text: str) -> list[float]:
        ...

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        ...


class OpenAIEmbedder:
    """OpenAI-based embedder using ``langchain_openai.OpenAIEmbeddings``."""

    def __init__(
        self,
        client: OpenAIEmbeddings | None = None,
        model: str = "text-embedding-3-small",
    ) -> None:
        self._client = client or get_embedding(model=model)

    async def embed(self, text: str) -> list[float]:
        return await self._client.aembed_query(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return await self._client.aembed_documents(texts)

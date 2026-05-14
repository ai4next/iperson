from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx


class PlatformClient(ABC):
    """Base class for platform API clients."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.client = httpx.AsyncClient(timeout=30.0)

    @abstractmethod
    async def publish(self, title: str, content: str, **kwargs: Any) -> dict[str, Any]:
        """Publish content to the platform. Returns result dict with status and url."""
        ...

    async def close(self) -> None:
        await self.client.aclose()
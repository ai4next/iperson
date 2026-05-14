from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from iperson.pipeline.context import PipelineContext


class StagePlugin(ABC):
    """Base class for all pipeline stage plugins."""

    plugin_id: str = ""
    name: str = ""
    description: str = ""
    category: str = ""  # discovery/research/generation/quality/publish
    version: str = "1.0.0"
    tags: list[str] = []
    config_schema: dict[str, Any] = {}
    default_config: dict[str, Any] = {}

    @abstractmethod
    async def execute(
        self, ctx: PipelineContext, config: dict[str, Any] | None = None
    ) -> PipelineContext:
        """Execute this stage and return the updated context."""
        ...

    async def on_register(self, registry: Any) -> None:
        """Called when the plugin is registered."""
        pass

    async def on_unregister(self) -> None:
        """Called when the plugin is unregistered."""
        pass
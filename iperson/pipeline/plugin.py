"""Base class for all pipeline stage plugins.

.. deprecated::
    Use deep agent nodes (``agent:`` in pipeline config) instead of
    ``StagePlugin`` subclasses. The agent-based pipeline provides
    skill loading, configurable models, and structured output parsing.
"""

from __future__ import annotations

import warnings
from abc import ABC, abstractmethod
from typing import Any

from iperson.pipeline.context import PipelineContext


class StagePlugin(ABC):
    """Base class for all pipeline stage plugins.

    .. deprecated::
        Use :class:`DeepAgentNode` instead. StagePlugin will be removed
        in a future version.
    """

    plugin_id: str = ""
    name: str = ""
    description: str = ""
    category: str = ""
    version: str = "1.0.0"
    tags: list[str] = []
    config_schema: dict[str, Any] = {}
    default_config: dict[str, Any] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        warnings.warn(
            f"StagePlugin ({cls.__name__}) is deprecated. "
            "Use deep agent nodes instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    @abstractmethod
    async def execute(
        self, ctx: PipelineContext, config: dict[str, Any] | None = None
    ) -> PipelineContext:
        """Execute this stage and return the updated context."""
        ...

    async def on_register(self, registry: Any) -> None:
        pass

    async def on_unregister(self) -> None:
        pass
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from iperson.pipeline.context import PipelineContext


@dataclass
class HookContext:
    pipeline_ctx: PipelineContext
    hook_point: str
    config: dict[str, Any] = field(default_factory=dict)


class BaseHook(ABC):
    hook_id: str = ""
    hook_point: str = ""
    name: str = ""
    description: str = ""
    version: str = "1.0.0"

    @abstractmethod
    async def execute(self, ctx: HookContext) -> HookContext:
        ...


class HookRegistry:
    def __init__(self) -> None:
        self._hooks: dict[str, type[BaseHook]] = {}

    def register(self, hook_class: type[BaseHook]) -> None:
        hook_id = hook_class.hook_id
        if not hook_id:
            raise ValueError("Hook must have a non-empty hook_id")
        self._hooks[hook_id] = hook_class

    def get_hooks_for_point(self, hook_point: str) -> list[type[BaseHook]]:
        return [
            cls for cls in self._hooks.values() if cls.hook_point == hook_point
        ]

    def list_hooks(self) -> list[dict[str, Any]]:
        return [
            {
                "hook_id": cls.hook_id,
                "hook_point": cls.hook_point,
                "name": cls.name,
                "description": cls.description,
                "version": cls.version,
            }
            for cls in self._hooks.values()
        ]

    def has(self, hook_id: str) -> bool:
        return hook_id in self._hooks
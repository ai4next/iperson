"""Registry for discovering and retrieving pipeline stage plugins.

.. deprecated::
    Use ``AgentRegistry`` instead.
"""

from __future__ import annotations

import warnings
from typing import Any

from iperson.pipeline.plugin import StagePlugin


class PluginRegistry:
    """Registry for discovering and retrieving pipeline stage plugins.

    .. deprecated::
        Use :class:`AgentRegistry` instead.
    """

    def __init__(self) -> None:
        warnings.warn(
            "PluginRegistry is deprecated. Use AgentRegistry instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._plugins: dict[str, type[StagePlugin]] = {}

    def register(self, plugin_class: type[StagePlugin]) -> None:
        """Register a plugin class by its plugin_id."""
        plugin_id = plugin_class.plugin_id
        if not plugin_id:
            raise ValueError("Plugin must have a non-empty plugin_id")
        self._plugins[plugin_id] = plugin_class

    def get(self, plugin_id: str) -> type[StagePlugin]:
        """Retrieve a plugin class by its plugin_id."""
        if plugin_id not in self._plugins:
            available = ", ".join(sorted(self._plugins.keys())) or "(none registered)"
            raise KeyError(
                f"Unknown plugin: '{plugin_id}'. Available plugins: {available}"
            )
        return self._plugins[plugin_id]

    def list_plugins(self) -> list[dict[str, Any]]:
        """List all registered plugins with their metadata."""
        return [
            {
                "plugin_id": cls.plugin_id,
                "name": cls.name,
                "description": cls.description,
                "category": cls.category,
                "version": cls.version,
            }
            for cls in self._plugins.values()
        ]

    def has(self, plugin_id: str) -> bool:
        """Check if a plugin is registered."""
        return plugin_id in self._plugins
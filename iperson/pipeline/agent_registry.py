"""Registry for deep agent node metadata.

Replaces PluginRegistry for agent-based pipeline nodes.
"""

from __future__ import annotations

from typing import Any


class AgentRegistry:
    """Registry for managing agent node metadata.

    Each entry describes a node type that can be used in a pipeline
    configuration. Agents are self-contained (configured via YAML),
    so the registry mainly serves discovery and documentation purposes.
    """

    def __init__(self) -> None:
        self._entries: dict[str, dict[str, Any]] = {}

    def register(
        self,
        node_id: str,
        *,
        description: str = "",
        category: str = "",
        default_prompt: str = "",
        default_model: str = "",
    ) -> None:
        """Register an agent node type."""
        self._entries[node_id] = {
            "node_id": node_id,
            "description": description,
            "category": category,
            "default_prompt": default_prompt,
            "default_model": default_model,
        }

    def get(self, node_id: str) -> dict[str, Any]:
        """Get metadata for a registered node."""
        if node_id not in self._entries:
            msg = f"Unknown agent node: '{node_id}'"
            raise KeyError(msg)
        return self._entries[node_id]

    def list_nodes(self) -> list[dict[str, Any]]:
        """List all registered agent nodes."""
        return list(self._entries.values())

    def has(self, node_id: str) -> bool:
        """Check if a node is registered."""
        return node_id in self._entries


__all__ = ["AgentRegistry"]
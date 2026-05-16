"""Tests for AgentRegistry."""

from __future__ import annotations

import pytest


def test_agent_registry_register_and_list() -> None:
    from iperson.pipeline.agent_registry import AgentRegistry

    reg = AgentRegistry()
    reg.register("research", description="Research agent", category="research")

    nodes = reg.list_nodes()
    assert len(nodes) == 1
    assert nodes[0]["node_id"] == "research"
    assert nodes[0]["description"] == "Research agent"


def test_agent_registry_get() -> None:
    from iperson.pipeline.agent_registry import AgentRegistry

    reg = AgentRegistry()
    reg.register("generate", description="Content generation")

    entry = reg.get("generate")
    assert entry["node_id"] == "generate"


def test_agent_registry_get_unknown() -> None:
    from iperson.pipeline.agent_registry import AgentRegistry

    reg = AgentRegistry()
    with pytest.raises(KeyError):
        reg.get("nonexistent")


def test_agent_registry_has() -> None:
    from iperson.pipeline.agent_registry import AgentRegistry

    reg = AgentRegistry()
    reg.register("research", description="test")

    assert reg.has("research")
    assert not reg.has("unknown")
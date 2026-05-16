"""Tests for deep agent pipeline integration."""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.messages import AIMessage

from iperson.pipeline.state import PipelineState


def _make_state(**overrides: Any) -> PipelineState:
    defaults: dict[str, Any] = dict(
        status="running",
        kb_chunks=[],
        kb_context="test kb",
        topic="test topic",
        generated_content="",
        platform_contents={},
        publish_results=[],
        errors=[],
        data={"user_key": "user_value"},
    )
    defaults.update(overrides)
    return PipelineState(**defaults)


@pytest.mark.asyncio
async def test_read_pipeline_returns_topic() -> None:
    from iperson.pipeline.agent_node import make_read_pipeline_tool

    state = _make_state(topic="AI 发展趋势")
    tool = make_read_pipeline_tool(state)
    result = await tool.ainvoke({"key": "topic"})
    assert result == "AI 发展趋势"


@pytest.mark.asyncio
async def test_read_pipeline_returns_kb_context() -> None:
    from iperson.pipeline.agent_node import make_read_pipeline_tool

    state = _make_state(kb_context="知识库内容")
    tool = make_read_pipeline_tool(state)
    result = await tool.ainvoke({"key": "kb_context"})
    assert result == "知识库内容"


@pytest.mark.asyncio
async def test_read_pipeline_data_dot_key() -> None:
    from iperson.pipeline.agent_node import make_read_pipeline_tool

    state = _make_state()
    tool = make_read_pipeline_tool(state)
    result = await tool.ainvoke({"key": "data.user_key"})
    assert result == "user_value"


@pytest.mark.asyncio
async def test_read_pipeline_missing_key_returns_none() -> None:
    from iperson.pipeline.agent_node import make_read_pipeline_tool

    state = _make_state()
    tool = make_read_pipeline_tool(state)
    result = await tool.ainvoke({"key": "nonexistent"})
    assert result is None


@pytest.mark.asyncio
async def test_deep_agent_node_parses_json_output() -> None:
    """DeepAgentNode should parse JSON from agent response and update state."""
    from iperson.pipeline.agent_node import DeepAgentNode

    async def fake_ainvoke(inputs: dict) -> dict:
        return {
            "messages": [
                AIMessage(content='```json\n{"generated_content": "hello"}\n```'),
            ]
        }

    node = DeepAgentNode(
        node_id="test-node",
        agent_ainvoke=fake_ainvoke,
        system_prompt="You are a test agent.",
        allowed_output_keys=["generated_content"],
    )

    state = _make_state()
    result = await node(state)

    assert result["generated_content"] == "hello"


@pytest.mark.asyncio
async def test_deep_agent_node_handles_agent_error() -> None:
    """DeepAgentNode should capture agent exceptions into errors list."""
    from iperson.pipeline.agent_node import DeepAgentNode

    async def failing_ainvoke(inputs: dict) -> dict:
        raise RuntimeError("Agent crashed")

    node = DeepAgentNode(
        node_id="test-node",
        agent_ainvoke=failing_ainvoke,
        system_prompt="test",
    )

    state = _make_state()
    result = await node(state)

    assert len(result["errors"]) == 1
    assert result["errors"][0]["node"] == "test-node"
    assert result["errors"][0]["error"] == "Agent crashed"
    assert result["status"] == "completed_with_errors"


@pytest.mark.asyncio
async def test_extract_json_from_fenced_block() -> None:
    from iperson.pipeline.agent_node import _extract_json

    text = 'Some text\n```json\n{"key": "value"}\n```\nmore text'
    result = _extract_json(text)
    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_extract_json_bare_object() -> None:
    from iperson.pipeline.agent_node import _extract_json

    result = _extract_json('{"key": "value"}')
    assert result == {"key": "value"}


@pytest.mark.asyncio
async def test_extract_json_no_json_returns_none() -> None:
    from iperson.pipeline.agent_node import _extract_json

    result = _extract_json("Just plain text without JSON")
    assert result is None


@pytest.mark.asyncio
async def test_agent_cache_hit_returns_same_instance() -> None:
    """AgentCache should return the same instance for same config."""
    from iperson.pipeline.agent_node import AgentCache

    cache = AgentCache()
    factory_call_count = 0

    async def factory():
        nonlocal factory_call_count
        factory_call_count += 1
        return "agent-instance"

    key = ("gpt-4o", "hash1", ("path/a", "path/b"))
    a = await cache.get_or_create(key, factory)
    b = await cache.get_or_create(key, factory)

    assert a is b
    assert factory_call_count == 1


@pytest.mark.asyncio
async def test_agent_cache_different_key_creates_new() -> None:
    from iperson.pipeline.agent_node import AgentCache

    cache = AgentCache()

    async def make_a():
        return "a"

    async def make_b():
        return "b"

    a = await cache.get_or_create(("model-a", "", ()), make_a)
    b = await cache.get_or_create(("model-b", "", ()), make_b)

    assert a == "a"
    assert b == "b"


@pytest.mark.asyncio
async def test_agent_cache_clear() -> None:
    from iperson.pipeline.agent_node import AgentCache

    cache = AgentCache()
    key = ("m", "h", ("s",))

    async def factory():
        return object()

    a = await cache.get_or_create(key, factory)
    cache.clear()
    b = await cache.get_or_create(key, factory)

    assert a is not b


def test_config_key_includes_model_prompt_and_skills() -> None:
    from iperson.pipeline.agent_node import config_key

    key = config_key("gpt-4o", "You are a test agent", ("sk1", "sk2"))
    assert len(key) == 3
    assert key[0] == "gpt-4o"
    assert isinstance(key[1], str)
    assert len(key[1]) == 16  # sha256 hex[:16]
    assert key[2] == ("sk1", "sk2")


@pytest.mark.asyncio
async def test_read_pipeline_via_state_ref_reflects_updates() -> None:
    """StateRef should allow read_pipeline to see updated state."""
    from iperson.pipeline.agent_node import StateRef, make_read_pipeline_tool

    ref = StateRef()
    ref.set({"topic": "initial"})
    tool = make_read_pipeline_tool(ref)

    result1 = await tool.ainvoke({"key": "topic"})
    assert result1 == "initial"

    ref.set({"topic": "updated"})
    result2 = await tool.ainvoke({"key": "topic"})
    assert result2 == "updated"


@pytest.mark.asyncio
async def test_deep_agent_node_with_state_ref_syncs_state() -> None:
    """DeepAgentNode should sync state to StateRef before calling agent."""
    from iperson.pipeline.agent_node import DeepAgentNode, StateRef

    captured: list[dict] = []

    async def capturing_ainvoke(inputs: dict) -> dict:
        # The agent would call read_pipeline here, but we capture instead
        captured.append(dict(inputs))
        return {"messages": [AIMessage(content='{"generated_content": "ok"}')]}

    ref = StateRef()
    ref.set({"topic": "before"})  # initial stale value

    node = DeepAgentNode(
        node_id="test",
        agent_ainvoke=capturing_ainvoke,
        system_prompt="test",
        state_ref=ref,
    )

    state = _make_state(topic="live-topic")
    await node(state)

    # After __call__, the ref should point to the live state
    assert ref.get()["topic"] == "live-topic"
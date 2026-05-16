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
"""Tests for deep agent pipeline integration."""

from __future__ import annotations

from typing import Any

import pytest

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
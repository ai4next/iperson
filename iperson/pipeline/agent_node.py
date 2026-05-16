"""Deep agent pipeline integration — DeepAgentNode, caching, and context tooling."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Awaitable, Callable
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool, tool


class StateRef:
    """Mutable reference to the current pipeline state dict.

    Allows a tool function to read the live state even when the enclosing
    agent is compiled once and cached across runs.
    """

    def __init__(self) -> None:
        self._state: dict[str, Any] = {}

    def set(self, state: dict[str, Any]) -> None:
        self._state = state

    def get(self) -> dict[str, Any]:
        return self._state


def _extract_json(text: str) -> dict[str, Any] | None:
    """Extract the first JSON object from agent response text."""
    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


class DeepAgentNode:
    """LangGraph node wrapper around a deep agent.

    Each instance manages a single deep agent (cached across pipeline runs).
    On each call it:
      1. Invokes the deep agent with system_prompt + pipeline context
      2. Parses structured JSON from the agent's final message
      3. Writes parsed fields back to PipelineState

    Note: Hooks (before/after) are handled by the caller in graph.py,
    which converts between PipelineState and PipelineContext.
    """

    def __init__(
        self,
        node_id: str,
        agent_ainvoke: Callable[[dict], Awaitable[dict]],
        system_prompt: str,
        allowed_output_keys: list[str] | None = None,
        state_ref: StateRef | None = None,
    ) -> None:
        self.node_id = node_id
        self._agent_ainvoke = agent_ainvoke
        self._system_prompt = system_prompt
        self._state_ref = state_ref
        self._allowed_output_keys = allowed_output_keys or [
            "kb_context",
            "generated_content",
            "platform_contents",
            "publish_results",
        ]

    async def __call__(self, state: dict[str, Any]) -> dict[str, Any]:
        # Sync mutable state reference so the agent's tools see live state
        if self._state_ref is not None:
            self._state_ref.set(state)

        task_parts = ["Current pipeline state:"]
        for key in ("topic", "kb_context"):
            if state.get(key):
                task_parts.append(f"  {key}: {state[key][:200]}")

        messages = [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content="\n".join(task_parts)),
        ]

        try:
            result = await self._agent_ainvoke({"messages": messages})
        except Exception as e:
            state.setdefault("errors", []).append({
                "node": self.node_id,
                "error": str(e),
                "recoverable": False,
            })
            state["status"] = "completed_with_errors"
            return state

        final_msg = result.get("messages", [])[-1] if result.get("messages") else None
        if isinstance(final_msg, AIMessage) and final_msg.content:
            parsed = _extract_json(str(final_msg.content))
            if parsed:
                for key in self._allowed_output_keys:
                    if key in parsed:
                        state[key] = parsed[key]
                if "data" in parsed and isinstance(parsed["data"], dict):
                    state.setdefault("data", {}).update(parsed["data"])
            else:
                state.setdefault("data", {})[f"{self.node_id}_raw_response"] = str(
                    final_msg.content
                )

        return state


def make_read_pipeline_tool(state: dict[str, Any] | StateRef) -> BaseTool:
    """Create a read_pipeline tool bound to the given pipeline state.

    Accepts either a plain ``dict`` (static, for testing) or a
    ``StateRef`` (mutable, for live pipeline runs).
    """

    def _resolve() -> dict[str, Any]:
        return state.get() if isinstance(state, StateRef) else state

    @tool
    async def read_pipeline(key: str) -> Any:
        """Read a value from the current pipeline context.

        Args:
            key: Field name to read. Use ``data.xxx`` for runtime KV values.
        """
        current = _resolve()
        if key.startswith("data."):
            data_key = key[5:]
            data: dict[str, Any] = current.get("data", {})
            return data.get(data_key)
        return current.get(key)

    return read_pipeline


class AgentCache:
    """Cache compiled deep agents by config fingerprint.

    Key: (model, system_prompt_hash, skills_tuple)
    """

    def __init__(self) -> None:
        self._cache: dict[tuple, Any] = {}

    async def get_or_create(
        self,
        key: tuple,
        factory: Callable[[], Awaitable[Any]],
    ) -> Any:
        if key not in self._cache:
            self._cache[key] = await factory()
        return self._cache[key]

    def clear(self) -> None:
        self._cache.clear()


def config_key(
    model: str | None,
    system_prompt: str,
    skills_sources: tuple[str, ...],
) -> tuple:
    """Build a cache key tuple from node config."""
    prompt_hash = hashlib.sha256(system_prompt.encode()).hexdigest()[:16]
    return (model or "", prompt_hash, skills_sources)


__all__ = [
    "DeepAgentNode",
    "_extract_json",
    "make_read_pipeline_tool",
    "AgentCache",
    "config_key",
]
"""Deep agent pipeline integration -- DeepAgentNode, caching, and context tooling."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


def make_read_pipeline_tool(state: dict[str, Any]) -> tool:
    """Create a read_pipeline tool bound to the given pipeline state dict.

    The returned tool is a LangChain BaseTool that reads fields from the
    pipeline state. Supports ``data.*`` for the runtime KV namespace.
    """

    @tool
    async def read_pipeline(key: str) -> Any:
        """Read a value from the current pipeline context.

        Args:
            key: Field name to read. Use ``data.xxx`` for runtime KV values.
        """
        if key.startswith("data."):
            data_key = key[5:]
            data: dict[str, Any] = state.get("data", {})
            return data.get(data_key)
        return state.get(key)

    return read_pipeline
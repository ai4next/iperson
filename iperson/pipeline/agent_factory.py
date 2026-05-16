"""Factory for creating DeepAgentNode instances from YAML config."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.skills import SkillsMiddleware

from iperson.pipeline.agent_node import (
    AgentCache,
    DeepAgentNode,
    StateRef,
    config_key,
    make_read_pipeline_tool,
)

_cache = AgentCache()


def load_prompt(path: str) -> str:
    """Load system prompt from a markdown file."""
    p = Path(path).expanduser()
    if not p.exists():
        msg = f"Prompt file not found: {p}"
        raise FileNotFoundError(msg)
    return p.read_text(encoding="utf-8")


def parse_skill_sources(
    skills_config: list[Any],
) -> list[tuple[str, str]]:
    """Parse skills config items into (path, label) tuples."""
    sources: list[tuple[str, str]] = []
    for item in skills_config:
        if isinstance(item, str):
            path = item
            label = Path(path).expanduser().name.replace("-", " ").title()
            sources.append((path, label))
        elif isinstance(item, dict):
            sources.append((item["source"], item.get("label", "")))
    return sources


def build_agent_node(
    node_id: str,
    agent_config: dict[str, Any],
    hook_orch: Any,
    state_provider: Any = None,
) -> DeepAgentNode:
    """Create a DeepAgentNode from a pipeline node's agent config.

    Args:
        node_id: Node identifier (e.g. ``"research"``).
        agent_config: The ``agent`` block from the pipeline YAML.
        hook_orch: HookOrchestrator instance for before/after hooks.
        state_provider: Optional callable returning current PipelineState.

    Returns:
        Configured DeepAgentNode ready to be used as a LangGraph node.
    """
    system_prompt = load_prompt(agent_config["prompt"])
    model = agent_config.get("model")

    skill_sources = parse_skill_sources(agent_config.get("skills", []))
    middleware: list[Any] = []
    if skill_sources:
        fs_backend = FilesystemBackend(virtual_mode=True)
        skills_mw = SkillsMiddleware(backend=fs_backend, sources=skill_sources)
        middleware.append(skills_mw)

    key = config_key(
        model,
        system_prompt,
        tuple(s[0] for s in skill_sources),
    )

    state_ref = StateRef()

    async def _build_agent() -> Any:
        """Create and return a compiled deep agent."""
        agent = create_deep_agent(
            model=model,
            system_prompt=system_prompt,
            middleware=middleware,
            tools=[make_read_pipeline_tool(state_ref)],
        )
        return agent

    async def _ainvoke(inputs: dict) -> dict:
        agent = await _cache.get_or_create(key, _build_agent)
        return await agent.ainvoke(inputs)

    return DeepAgentNode(
        node_id=node_id,
        agent_ainvoke=_ainvoke,
        system_prompt=system_prompt,
        allowed_output_keys=agent_config.get(
            "output_keys",
            ["kb_context", "generated_content", "platform_contents", "publish_results"],
        ),
        state_ref=state_ref,
    )


__all__ = [
    "load_prompt",
    "parse_skill_sources",
    "build_agent_node",
]
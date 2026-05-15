from __future__ import annotations

from iperson.pipeline.hook import HookRegistry


def register_builtin_hooks(registry: HookRegistry) -> None:
    """Register all built-in hooks with the given registry."""
    from iperson.pipeline.hooks.trending_inject import TrendingInjectHook

    registry.register(TrendingInjectHook)


__all__ = ["register_builtin_hooks"]
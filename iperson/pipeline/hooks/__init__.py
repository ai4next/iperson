from __future__ import annotations

from iperson.pipeline.hook import HookRegistry


def register_builtin_hooks(registry: HookRegistry) -> None:
    from iperson.pipeline.hooks.trending_inject import TrendingInjectHook
    from iperson.pipeline.hooks.prompt_guard import PromptGuardHook
    from iperson.pipeline.hooks.content_scan import ContentScanHook

    registry.register(TrendingInjectHook)
    registry.register(PromptGuardHook)
    registry.register(ContentScanHook)


__all__ = ["register_builtin_hooks"]
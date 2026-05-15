from __future__ import annotations

from iperson.pipeline.hook import HookRegistry


def register_builtin_hooks(registry: HookRegistry) -> None:
    from iperson.pipeline.hooks.trending_inject import TrendingInjectHook
    from iperson.pipeline.hooks.prompt_guard import PromptGuardHook
    from iperson.pipeline.hooks.content_scan import ContentScanHook
    from iperson.pipeline.hooks.seo_analyze import SeoAnalyzeHook
    from iperson.pipeline.hooks.image_gen import ImageGenHook

    registry.register(TrendingInjectHook)
    registry.register(PromptGuardHook)
    registry.register(ContentScanHook)
    registry.register(SeoAnalyzeHook)
    registry.register(ImageGenHook)


__all__ = ["register_builtin_hooks"]
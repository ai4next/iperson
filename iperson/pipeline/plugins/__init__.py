from __future__ import annotations

from iperson.pipeline.plugins.generation.article import ArticleGenerationPlugin
from iperson.pipeline.plugins.publish.multiplatform import MultiplatformPublishPlugin
from iperson.pipeline.plugins.quality.humanizer import HumanizerPlugin
from iperson.pipeline.plugins.research.kb_retrieve import KbRetrievePlugin
from iperson.pipeline.registry import PluginRegistry


def register_builtin_plugins(registry: PluginRegistry) -> None:
    """Register all built-in pipeline plugins with the given registry."""
    registry.register(KbRetrievePlugin)
    registry.register(ArticleGenerationPlugin)
    # HumanizerPlugin removed (now a hook)
    # AuditPlugin removed
    registry.register(MultiplatformPublishPlugin)


__all__ = [
    "KbRetrievePlugin",
    "ArticleGenerationPlugin",
    "HumanizerPlugin",
    "MultiplatformPublishPlugin",
    "register_builtin_plugins",
]
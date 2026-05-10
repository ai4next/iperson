"""Publish Hub — plugin-based multi-platform publishing abstraction.

Extends IPulse's BasePlatform / PlatformRegistry pattern.
Each platform adapter implements the BasePlatform ABC.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PublishResult:
    post_id: str = ""
    url: str = ""
    status: str = "pending"  # pending | published | failed
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


class BasePlatform(ABC):
    """Abstract base for all social-media platform adapters."""

    name: str = ""

    @abstractmethod
    async def authenticate(self) -> bool:
        """Verify credentials are valid for this platform."""
        ...

    @abstractmethod
    async def publish(self, content: str, media: list[str] | None = None) -> PublishResult:
        """Publish content to the platform."""
        ...

    @abstractmethod
    async def validate_content(self, content: str) -> tuple[bool, str]:
        """Check content meets platform constraints before publishing."""
        ...

    @abstractmethod
    async def get_metrics(self, post_id: str) -> dict[str, Any]:
        """Retrieve engagement metrics for a published post."""
        ...

    @abstractmethod
    async def delete(self, post_id: str) -> bool:
        """Remove a published post from the platform."""
        ...


class PlatformRegistry:
    """Decorator-based plugin registry (replicates IPulse pattern)."""

    _platforms: dict[str, type[BasePlatform]] = {}

    @classmethod
    def register(cls, name: str):
        def _inner(klass: type[BasePlatform]) -> type[BasePlatform]:
            klass.name = name
            cls._platforms[name] = klass
            return klass
        return _inner

    @classmethod
    def get(cls, name: str) -> type[BasePlatform]:
        platform = cls._platforms.get(name)
        if platform is None:
            raise KeyError(f"Unknown platform: '{name}'. Available: {list(cls._platforms)}")
        return platform

    @classmethod
    def list_available(cls) -> list[str]:
        return list(cls._platforms)


# ── Built-in: Dry-run platform ─────────────────────────────────────────

@PlatformRegistry.register("dry_run")
class DryRunPlatform(BasePlatform):
    """Write content to local files instead of publishing."""

    name = "dry_run"

    async def authenticate(self) -> bool:
        return True

    async def publish(self, content: str, media: list[str] | None = None) -> PublishResult:
        import uuid
        from datetime import UTC, datetime

        path = f"output/dry_run/{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.md"
        with open(path, "w") as f:
            f.write(content)
        return PublishResult(post_id=path, url=f"file://{path}", status="published")

    async def validate_content(self, content: str) -> tuple[bool, str]:
        return (len(content.strip()) > 0, "Content is empty" if not content.strip() else "")

    async def get_metrics(self, post_id: str) -> dict[str, Any]:
        return {}

    async def delete(self, post_id: str) -> bool:
        import os
        try:
            os.remove(post_id)
            return True
        except FileNotFoundError:
            return False


# ── Platform-specific adapters (stubs for future implementation) ───────

# @PlatformRegistry.register("xiaohongshu")
# class XiaohongshuPlatform(BasePlatform):
#     name = "xiaohongshu"
#     # TODO: implement with 小红书开放平台 API

# @PlatformRegistry.register("weibo")
# class WeiboPlatform(BasePlatform):
#     name = "weibo"
#     # TODO: implement with 微博开放平台 API

# @PlatformRegistry.register("twitter")
# class TwitterPlatform(BasePlatform):
#     name = "twitter"
#     # Migrate from IPulse's publishing/twitter.py (uses tweepy)
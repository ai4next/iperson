from __future__ import annotations

import pytest

from iperson.publish.platforms.base import PlatformClient
from iperson.publish.platforms import get_platform_client, PLATFORM_REGISTRY


class TestPlatformRegistry:
    def test_all_platforms_registered(self) -> None:
        assert "zhihu" in PLATFORM_REGISTRY
        assert "weibo" in PLATFORM_REGISTRY
        assert "douyin" in PLATFORM_REGISTRY

    def test_get_platform_client(self) -> None:
        client = get_platform_client("zhihu")
        assert client is not None

    def test_unknown_platform_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown platform"):
            get_platform_client("nonexistent")
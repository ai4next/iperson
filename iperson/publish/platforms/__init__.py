from __future__ import annotations

from typing import Any

from iperson.publish.platforms.douyin import DouyinClient
from iperson.publish.platforms.weibo import WeiboClient
from iperson.publish.platforms.zhihu import ZhihuClient

PLATFORM_REGISTRY: dict[str, type] = {
    "zhihu": ZhihuClient,
    "weibo": WeiboClient,
    "douyin": DouyinClient,
}


def get_platform_client(platform: str, config: dict[str, Any] | None = None) -> Any:
    """Get a platform client instance by name."""
    client_class = PLATFORM_REGISTRY.get(platform)
    if client_class is None:
        raise ValueError(f"Unknown platform: {platform}. Available: {list(PLATFORM_REGISTRY.keys())}")
    return client_class(config)
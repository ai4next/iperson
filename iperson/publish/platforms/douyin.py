from __future__ import annotations

from typing import Any

from iperson.publish.platforms.base import PlatformClient


class DouyinClient(PlatformClient):
    """Douyin (抖音) content publisher."""

    BASE_URL = "https://open.douyin.com"

    async def publish(self, title: str, content: str, **kwargs: Any) -> dict[str, Any]:
        """Publish content to Douyin."""
        access_token = self.config.get("access_token", "")

        try:
            resp = await self.client.post(
                f"{self.BASE_URL}/api/douyin/v1/video/upload/",
                headers={"access-token": access_token},
                json={"title": title, "content": content},
            )
            resp.raise_for_status()
            data = resp.json()
            return {"status": "ok", "url": f"https://www.douyin.com/video/{data.get('item_id', '')}", "platform": "douyin"}
        except Exception as e:
            return {"status": "failed", "error": str(e), "platform": "douyin"}
from __future__ import annotations

from typing import Any

from iperson.publish.platforms.base import PlatformClient


class WeiboClient(PlatformClient):
    """Weibo (微博) content publisher."""

    BASE_URL = "https://api.weibo.com"

    async def publish(self, title: str, content: str, **kwargs: Any) -> dict[str, Any]:
        """Post a Weibo status."""
        access_token = self.config.get("access_token", "")

        # Weibo text posts have a 2000 char limit
        text = f"{title}\n\n{content}"[:2000]

        try:
            resp = await self.client.post(
                f"{self.BASE_URL}/2/statuses/share.json",
                params={"access_token": access_token, "status": text},
            )
            resp.raise_for_status()
            data = resp.json()
            return {"status": "ok", "url": f"https://weibo.com/{data.get('id', '')}", "platform": "weibo"}
        except Exception as e:
            return {"status": "failed", "error": str(e), "platform": "weibo"}
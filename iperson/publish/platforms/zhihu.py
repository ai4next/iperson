from __future__ import annotations

from typing import Any

from iperson.publish.platforms.base import PlatformClient


class ZhihuClient(PlatformClient):
    """Zhihu (知乎) content publisher using the Zhihu API."""

    BASE_URL = "https://zhuanlan.zhihu.com"

    async def publish(self, title: str, content: str, **kwargs: Any) -> dict[str, Any]:
        """Publish an article to Zhihu column."""
        cookie = self.config.get("cookie", "")
        token = self.config.get("token", "")

        headers = {"Cookie": cookie, "X-XSRF-TOKEN": token, "Content-Type": "application/json"}

        payload = {"title": title, "content": content, "column_slug": self.config.get("column_slug", "")}

        # In real usage this would POST to the Zhihu API
        # For now, simulate the API call structure
        try:
            resp = await self.client.post(
                f"{self.BASE_URL}/api/articles",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return {"status": "ok", "url": f"{self.BASE_URL}/p/{data.get('id', '')}", "platform": "zhihu"}
        except Exception as e:
            return {"status": "failed", "error": str(e), "platform": "zhihu"}

    async def get_column_info(self) -> dict[str, Any]:
        """Get Zhihu column information."""
        resp = await self.client.get(f"{self.BASE_URL}/api/columns/{self.config.get('column_slug', '')}")
        resp.raise_for_status()
        return resp.json()
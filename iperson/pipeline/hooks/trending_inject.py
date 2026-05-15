from __future__ import annotations

from iperson.pipeline.hook import BaseHook, HookContext


class TrendingInjectHook(BaseHook):
    hook_id: str = "intelligence.trending_inject"
    hook_point: str = "before.generation"
    name: str = "Trending Inject"
    description: str = "Fetch trending topics and inject into generation context"

    async def execute(self, ctx: HookContext) -> HookContext:
        trending = await self._fetch_trending(ctx.config.get("source", "zhihu"))
        ctx.pipeline_ctx.data["trending_data"] = trending
        return ctx

    async def _fetch_trending(self, source: str) -> list[dict[str, str]]:
        """Fetch trending topics from external sources.

        Returns empty list on failure — never blocks the pipeline.
        """
        try:
            if source == "zhihu":
                return await self._fetch_zhihu_hot()
            elif source == "weibo":
                return await self._fetch_weibo_hot()
            return []
        except Exception:
            return []

    async def _fetch_zhihu_hot(self) -> list[dict[str, str]]:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                {"title": item["target"]["title"], "url": item["target"]["url"]}
                for item in data.get("data", [])[:10]
            ]

    async def _fetch_weibo_hot(self) -> list[dict[str, str]]:
        import httpx

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://weibo.com/ajax/side/hotSearch")
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "title": item["word"],
                    "url": f"https://s.weibo.com/weibo?q={item['word']}",
                }
                for item in data.get("data", {}).get("realtime", [])[:10]
            ]
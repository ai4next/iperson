from __future__ import annotations

from typing import Any

from iperson.pipeline.hook import BaseHook, HookContext


class PlatformizeHook(BaseHook):
    hook_id = "quality.platformize"
    hook_point = "before.publish"
    name = "Platformize"
    description = "Adapt generated content for each target platform's style"

    async def execute(self, ctx: HookContext) -> HookContext:
        content = ctx.pipeline_ctx.generated_content
        if not content:
            return ctx

        platforms: list[str] = ctx.config.get("platforms", [])
        llm_client = ctx.pipeline_ctx.data.get("llm_client")
        persona_engine = ctx.pipeline_ctx.data.get("persona_engine")

        platform_contents: dict[str, str] = {}

        for platform in platforms:
            platform_content = await self._adapt_for_platform(
                content=content,
                platform=platform,
                llm_client=llm_client,
                persona_engine=persona_engine,
            )
            platform_contents[platform] = platform_content

        ctx.pipeline_ctx.platform_contents = platform_contents
        return ctx

    async def _adapt_for_platform(
        self,
        content: str,
        platform: str,
        llm_client: Any,
        persona_engine: Any,
    ) -> str:
        """Adapt content for a specific platform's style.

        Uses platform-specific prompt templates to rewrite the content.
        Falls back to the original content if no LLM client is available.
        """
        if llm_client is None:
            return content

        platform_styles = {
            "xiaohongshu": "小红书风格：短句、口语化、适当使用emoji、要点列表、亲和力强",
            "wechat": "微信公众号风格：长文深度分析、段落叙事、引言+小标题结构、专业但有温度",
            "zhihu": "知乎风格：专业严谨、结构化论证、引用来源、第一人称经验分享",
        }

        style_guide = platform_styles.get(platform, f"{platform}平台风格")
        persona_context = ""
        if persona_engine:
            persona_context = f"\n人设信息：\n{persona_engine.build_system_prompt()}"

        prompt = (
            f"请将以下文章改写为{style_guide}。\n"
            f"保留原文的核心信息和观点，只调整表达方式。\n"
            f"{persona_context}\n"
            f"---\n{content}\n---\n"
            f"请直接输出改写后的内容，不要加额外说明。"
        )

        messages = [{"role": "user", "content": prompt}]
        response = await llm_client.ainvoke(messages)
        return response.content.strip() or content
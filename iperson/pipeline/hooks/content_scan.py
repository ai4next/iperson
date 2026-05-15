from __future__ import annotations

from iperson.core.security.wordlist import load_blocked_words
from iperson.pipeline.hook import BaseHook, HookContext


class ContentScanHook(BaseHook):
    hook_id: str = "safety.content_scan"
    hook_point: str = "after.generation"
    name: str = "Content Scan"
    description: str = "Scan generated content for banned words and patterns"

    async def execute(self, ctx: HookContext) -> HookContext:
        content = ctx.pipeline_ctx.generated_content
        if not content:
            return ctx

        blocked_words = load_blocked_words()
        content_lower = content.lower()
        found = [w for w in blocked_words if w.lower() in content_lower]

        ctx.pipeline_ctx.data["scan_result"] = {
            "banned_found": bool(found),
            "banned_words": found[:10],
            "total_banned": len(found),
        }
        return ctx
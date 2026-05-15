from __future__ import annotations

import hashlib
import hmac
import json

import httpx

from iperson.config import load_config
from iperson.pipeline.hook import BaseHook, HookContext


class WebhookNotifyHook(BaseHook):
    hook_id: str = "webhook.notify"
    hook_point: str = "after.publish"
    name: str = "Webhook Notify"
    description: str = "Send HTTP notifications on pipeline events"

    async def execute(self, ctx: HookContext) -> HookContext:
        config = load_config()
        webhooks = config.get("webhooks", [])
        if not webhooks:
            ctx.pipeline_ctx.data["webhook_notified"] = False
            return ctx

        payload = {
            "event": "pipeline.complete",
            "topic": ctx.pipeline_ctx.topic,
            "status": ctx.pipeline_ctx.status,
            "content_id": ctx.pipeline_ctx.content_id,
            "errors": [str(e) for e in ctx.pipeline_ctx.errors],
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            for wh in webhooks:
                url = wh.get("url", "")
                secret = wh.get("secret", "")
                if not url:
                    continue
                try:
                    body = json.dumps(payload, ensure_ascii=False).encode()
                    headers = {"Content-Type": "application/json"}
                    if secret:
                        sig = hmac.new(
                            secret.encode(), body, hashlib.sha256
                        ).hexdigest()
                        headers["X-Webhook-Signature"] = sig
                    await client.post(url, content=body, headers=headers)
                except Exception:
                    pass  # Never let webhook failure affect the pipeline

        ctx.pipeline_ctx.data["webhook_notified"] = True
        return ctx
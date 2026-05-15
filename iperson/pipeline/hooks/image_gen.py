from __future__ import annotations

from pathlib import Path

from iperson.config import load_config
from iperson.pipeline.hook import BaseHook, HookContext


class ImageGenHook(BaseHook):
    hook_id: str = "media.image_gen"
    hook_point: str = "before.publish"
    name: str = "Image Generation"
    description: str = "Generate cover image and inline illustrations for content"

    async def execute(self, ctx: HookContext) -> HookContext:
        content = ctx.pipeline_ctx.generated_content
        if not content:
            ctx.pipeline_ctx.data["images_generated"] = False
            return ctx

        provider_name = ctx.config.get("provider", "openai")
        style = ctx.config.get("style", "flat illustration, warm tones")
        count = int(ctx.config.get("count", 2))
        cover = bool(ctx.config.get("cover", True))

        output_dir = (
            Path(ctx.pipeline_ctx.data.get("output_dir", ".")) / "media"
        )

        if provider_name == "openai":
            config = load_config()
            api_key = config.get("llm", {}).get("api_key", "")
            if not api_key:
                ctx.pipeline_ctx.data["images_generated"] = False
                return ctx

            from iperson.core.media.providers.openai import OpenAIImageProvider

            provider = OpenAIImageProvider(api_key=api_key)

            try:
                # Generate cover image
                if cover:
                    cover_prompt = (
                        f"{style} Cover image for article about:"
                        f" {ctx.pipeline_ctx.topic}"
                    )
                    cover_path = await provider.generate(
                        prompt=cover_prompt,
                        size="1792x1024",
                        output_dir=output_dir,
                    )
                    if cover_path:
                        ctx.pipeline_ctx.data["cover_image"] = str(cover_path)

                # Generate inline images
                images = []
                for i in range(count):
                    img_prompt = (
                        f"{style} Illustration {i+1} for:"
                        f" {ctx.pipeline_ctx.topic}"
                    )
                    path = await provider.generate(
                        prompt=img_prompt,
                        size="1024x1024",
                        output_dir=output_dir,
                    )
                    if path:
                        images.append(str(path))

                ctx.pipeline_ctx.data["inline_images"] = images
                ctx.pipeline_ctx.data["images_generated"] = True
            finally:
                await provider.close()
        else:
            ctx.pipeline_ctx.data["images_generated"] = False

        return ctx
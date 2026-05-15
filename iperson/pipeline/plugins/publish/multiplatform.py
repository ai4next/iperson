from __future__ import annotations

from typing import Any

from iperson.pipeline.context import PipelineContext
from iperson.pipeline.plugin import StagePlugin
from iperson.utils.output import (
    create_output_dir,
    write_article,
    write_platform_content,
)


class MultiplatformPublishPlugin(StagePlugin):
    """Publish content to one or more target platforms."""

    plugin_id: str = "publish.multiplatform"
    name: str = "Multi-Platform Publish"
    description: str = "Write article, audit report, and platform-specific content files"
    category: str = "publish"
    version: str = "1.0.0"
    default_config: dict[str, Any] = {
        "platforms": ["xiaohongshu"],
    }

    async def execute(
        self, ctx: PipelineContext, config: dict[str, Any] | None = None
    ) -> PipelineContext:
        """Write content to disk for each target platform.

        Uses ``ctx.platform_contents`` for per-platform content, falls back to
        ``ctx.generated_content`` for missing platforms.

        Config:
            - ``platforms``: List of platform names (default ``["xiaohongshu"]``).

        Sets:
            - ``ctx.publish_results``: List of per-platform publish records.
            - ``ctx.data["output_dir"]``: The output directory path.
        """
        merged = {**self.default_config, **(config or {})}
        platforms: list[str] = merged["platforms"]

        out_dir = create_output_dir(ctx.topic)
        ctx.data["output_dir"] = str(out_dir)

        # Write core article
        write_article(out_dir, ctx.generated_content)

        # Write platform-specific content
        publish_results: list[dict[str, Any]] = []
        for platform in platforms:
            # Use platform_contents if available, fall back to generated_content
            content = ctx.platform_contents.get(platform, ctx.generated_content)
            platform_path = write_platform_content(out_dir, platform, content)
            publish_results.append(
                {
                    "platform": platform,
                    "path": str(platform_path),
                    "status": "ready",
                }
            )

        ctx.publish_results = publish_results

        return ctx
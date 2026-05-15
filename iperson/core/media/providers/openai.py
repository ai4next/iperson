from __future__ import annotations

from pathlib import Path

import httpx


class OpenAIImageProvider:
    """Generate images using OpenAI DALL-E API."""

    def __init__(self, api_key: str, model: str = "dall-e-3") -> None:
        self.api_key = api_key
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate(
        self,
        prompt: str,
        size: str = "1792x1024",
        quality: str = "standard",
        output_dir: Path | None = None,
    ) -> Path | None:
        """Generate an image and save to disk. Returns path or None on failure."""
        try:
            resp = await self.client.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "n": 1,
                    "size": size,
                    "quality": quality,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            image_url = data["data"][0]["url"]

            # Download the image
            img_resp = await self.client.get(image_url)
            img_resp.raise_for_status()

            output_dir = output_dir or Path(".")
            output_dir.mkdir(parents=True, exist_ok=True)
            ext = "png"
            path = output_dir / f"img_{hash(prompt) & 0xffffffff:x}.{ext}"
            path.write_bytes(img_resp.content)
            return path
        except Exception:
            return None

    async def close(self) -> None:
        await self.client.aclose()
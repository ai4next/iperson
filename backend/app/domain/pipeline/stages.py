"""LLM-powered pipeline stages — Generation & Ranking.

These stages implement StageProtocol and use LangChain for LLM calls.
Extends IPulse's content/generator.py patterns.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings
from app.domain.pipeline import PipelineContext, StageProtocol

logger = logging.getLogger(__name__)


def _get_llm(task: str) -> Any:
    """Create an LLM instance for the given task.

    This is a simplified version of IPulse's ModelFactory.
    In production this would use the ModelRouter with fallback/cost optimisation.
    """
    configs = {
        "topic_ranking": {"model": "gpt-4o-mini", "provider": "openai", "temperature": 0.1},
        "content_generation": {
            "model": "claude-sonnet-4-20250514",
            "provider": "anthropic",
            "temperature": 0.7,
        },
        "quality_check": {"model": "gpt-4o-mini", "provider": "openai", "temperature": 0.0},
        "style_analysis": {"model": "claude-sonnet-4-20250514", "provider": "anthropic", "temperature": 0.3},
    }

    cfg = configs.get(task, configs["content_generation"])

    if cfg["provider"] == "openai":
        return ChatOpenAI(
            model=cfg["model"],
            temperature=cfg["temperature"],
            api_key=settings.openai_api_key or None,
        )
    elif cfg["provider"] == "anthropic":
        return ChatAnthropic(
            model=cfg["model"],
            temperature=cfg["temperature"],
            api_key=settings.anthropic_api_key or None,
        )
    raise ValueError(f"Unknown provider: {cfg['provider']}")


class GenerationStage(StageProtocol):
    """Pipeline stage: generate content from a selected topic using LLM."""

    name = "generation"

    def __init__(self, persona_prompts: list[dict[str, str]] | None = None) -> None:
        self._persona_prompts = persona_prompts

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.selected_topic:
            logger.warning("No topic selected, skipping generation")
            return ctx

        if self._persona_prompts:
            messages = self._persona_prompts
        else:
            messages = await self._build_default_prompt(ctx.selected_topic)

        llm = _get_llm("content_generation")
        response = await llm.ainvoke(
            [SystemMessage(content=messages[0]["content"])] +
            [HumanMessage(content=messages[1]["content"])]
        )

        ctx.draft_content = response.content
        logger.info(f"Generated content: {len(ctx.draft_content)} chars")
        return ctx

    async def _build_default_prompt(self, topic: dict[str, Any]) -> list[dict[str, str]]:
        """Fallback prompt generation when persona prompts aren't provided."""
        return [
            {
                "role": "system",
                "content": "You are a creative content writer who produces engaging social media posts."
                " Write with a distinct personal voice — insightful, authentic, and conversational.",
            },
            {
                "role": "user",
                "content": (
                    f"Topic: {topic.get('title', '')}\n"
                    f"Summary: {topic.get('summary', '')}\n\n"
                    "Write an engaging social media post about this topic. "
                    "Include a hook, personal insight, and 2-3 relevant hashtags."
                ),
            },
        ]


class RankingStage(StageProtocol):
    """Pipeline stage: rank discovered topics using LLM-as-judge."""

    name = "ranking"

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.topics:
            logger.warning("No topics to rank")
            return ctx

        llm = _get_llm("topic_ranking")
        topic_text = "\n".join(
            f"- {t.get('title', '')} | source={t.get('source', '')} | heat={t.get('heat_score', 0):.2f}"
            for t in ctx.topics[:20]
        )

        response = await llm.ainvoke([
            SystemMessage(content=(
                "You are a content strategist. Score each topic for social media relevance on a scale of 0-10. "
                "Consider: novelty, audience engagement potential, and timeliness. "
                "Return ONLY a valid JSON array of objects with 'title' and 'score' fields."
            )),
            HumanMessage(content=f"Topics to rank:\n{topic_text}"),
        ])

        try:
            scored = json.loads(response.content)
            if isinstance(scored, list) and scored:
                scored.sort(key=lambda x: x.get("score", 0), reverse=True)
                top = scored[0].get("title", "")
                ctx.selected_topic = next(
                    (t for t in ctx.topics if t.get("title") == top),
                    ctx.topics[0],
                )
        except (json.JSONDecodeError, IndexError):
            ctx.selected_topic = ctx.topics[0] if ctx.topics else None

        return ctx


class DiscoveryStage(StageProtocol):
    """Pipeline stage: discover trending topics from external sources.

    Mirrors IPulse's discovery/aggregator.py pattern.
    Sources are configured per persona (hackernews, zhihu, weibo hot, etc.)
    """

    name = "discovery"

    def __init__(self, sources: list[str] | None = None, max_topics: int = 20) -> None:
        self.sources = sources or ["hackernews"]
        self._max_topics = max_topics

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        topics: list[dict[str, Any]] = []

        for source_name in self.sources:
            try:
                source_topics = await self._fetch_from_source(source_name)
                topics.extend(source_topics)
                logger.info(f"Discovered {len(source_topics)} topics from {source_name}")
            except Exception as exc:
                ctx.errors.append({
                    "stage": self.name, "source": source_name,
                    "error": str(exc), "time": str(datetime.now(UTC)),
                })

        # Deduplicate by title
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for t in topics:
            key = t.get("title", "")
            if key and key not in seen:
                seen.add(key)
                unique.append(t)

        # Sort by heat score, limit
        unique.sort(key=lambda t: t.get("heat_score", 0) or 0, reverse=True)
        ctx.topics = unique[:self._max_topics]
        logger.info(f"Discovery complete: {len(ctx.topics)} unique topics")
        return ctx

    async def _fetch_from_source(self, source: str) -> list[dict[str, Any]]:
        """Fetch topics from a single source.

        Production implementation would use IPulse's BaseSource adapters.
        This provides a minimal httpx-based implementation for HackerNews.
        """
        if source == "hackernews":
            import httpx

            async with httpx.AsyncClient() as client:
                # Fetch top story IDs
                resp = await client.get(
                    "https://hacker-news.firebaseio.com/v0/topstories.json",
                    timeout=15,
                )
                ids = resp.json()[:30]

                # Fetch details
                topics = []
                for sid in ids:
                    try:
                        r = await client.get(
                            f"https://hacker-news.firebaseio.com/v0/item/{sid}.json",
                            timeout=10,
                        )
                        item = r.json()
                        if item and item.get("title") and item.get("score", 0) >= 50:
                            topics.append({
                                "title": item["title"],
                                "url": item.get("url", f"https://news.ycombinator.com/item?id={sid}"),
                                "summary": item.get("title", ""),
                                "source": "hackernews",
                                "source_id": str(sid),
                                "heat_score": min(item.get("score", 0) / 100, 1.0),
                                "comment_count": item.get("descendants", 0),
                            })
                    except Exception:
                        continue
                return topics

        elif source == "zhihu":
            logger.warning("Zhihu source not yet implemented — requires API credentials")
            return []

        logger.warning(f"Unknown source: {source}")
        return []


class QualityGateStage(StageProtocol):
    """Pipeline stage: validate generated content quality.

    Extends IPulse's content/quality.py patterns — rule-based + optional LLM check.
    """

    name = "quality_gate"

    def __init__(self, quality_threshold: float = 0.7) -> None:
        self._threshold = quality_threshold

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        content = ctx.draft_content or ""
        issues: list[dict[str, Any]] = []

        # 1. Length checks
        if len(content) < 20:
            issues.append({"type": "too_short", "detail": f"Content too short: {len(content)} chars", "score_delta": -0.3})
        if len(content) > 5000:
            issues.append({"type": "too_long", "detail": f"Content exceeds 5000 chars: {len(content)}", "score_delta": -0.1})

        # 2. Placeholder detection (from IPulse)
        placeholder_patterns = ["[INSERT", "[TODO", "[PLACEHOLDER", "{{", "]]", "ADD_CONTENT"]
        for pattern in placeholder_patterns:
            if pattern in content:
                issues.append({"type": "placeholder", "detail": f"Contains placeholder: '{pattern}'", "score_delta": -0.2})

        # 3. Hashtag check for social content
        if "#" not in content:
            issues.append({"type": "missing_hashtags", "detail": "No hashtags found", "score_delta": -0.1})

        # Calculate final score
        score = 1.0
        for issue in issues:
            score += issue.get("score_delta", 0)
        score = max(0.0, score)

        ctx.quality_results = issues
        ctx.draft_content = content  # pass through

        if score < self._threshold:
            logger.warning(f"Quality score {score:.2f} below threshold {self._threshold}: {len(issues)} issues")
        else:
            logger.info(f"Quality gate passed: score={score:.2f}")

        return ctx


class AdaptationStage(StageProtocol):
    """Pipeline stage: adapt draft content for each target platform.

    Each platform has unique constraints (character limits, formatting,
    media requirements).  This stage produces platform-specific versions
    of the draft content (e.g., truncate for Twitter, add emoji for
    Xiaohongshu, format as thread for Weibo).
    """

    name = "adaptation"

    def __init__(self, platforms: list[str] | None = None) -> None:
        self._platforms = platforms or ["xiaohongshu"]

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        content = ctx.draft_content or ""
        if not content:
            logger.warning("No draft content to adapt")
            return ctx

        for platform in self._platforms:
            try:
                adapted = self._adapt_for_platform(content, platform)
                ctx.adapted_content[platform] = adapted
                logger.info(f"Adapted content for {platform}: {len(adapted)} chars")
            except Exception as exc:
                ctx.errors.append({
                    "stage": self.name, "platform": platform,
                    "error": str(exc), "time": str(datetime.now(UTC)),
                })

        return ctx

    def _adapt_for_platform(self, content: str, platform: str) -> str:
        """Apply platform-specific formatting rules.

        Production implementation would use the BaseContentAdapter pattern
        from IPulse's content/adapters/ module.
        """
        if platform == "twitter":
            # Twitter: 280 char limit with URL reservation
            max_len = 280 - 23  # 23 chars reserved for link
            if len(content) > max_len:
                return content[:max_len].rsplit(" ", 1)[0] + "…"
            return content

        if platform == "xiaohongshu":
            # Xiaohongshu: emoji-rich, with hashtags, 1000 char limit
            if len(content) > 1000:
                return content[:997] + "…"
            return content

        if platform == "weibo":
            # Weibo: 2000 char limit
            if len(content) > 2000:
                return content[:1997] + "…"
            return content

        if platform == "wechat":
            # WeChat: long-form, add separator
            return content + "\n\n---\n#iperson #AI创作"

        # Default: pass through
        return content
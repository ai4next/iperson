"""Celery worker — async task execution for content pipeline & scheduling."""

from __future__ import annotations

import asyncio
import logging

from celery import Celery, Task

from app.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "iperson",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


def _run_async(coro):
    """Run an async coroutine in the Celery sync task context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3, soft_time_limit=300)
def run_content_pipeline(self: Task, tenant_id: str, persona_id: str) -> dict:
    """Execute the full content pipeline for a persona.

    Orchestrates: Discovery → Ranking → Generation → Adaptation → QualityGate.
    """
    from app.domain import (
        AdaptationStage,
        DiscoveryStage,
        GenerationStage,
        PipelineContext,
        PipelineOrchestrator,
        QualityGateStage,
        RankingStage,
    )

    # Build pipeline with all stages
    stages = [
        DiscoveryStage(sources=["hackernews"]),
        RankingStage(),
        GenerationStage(),
        AdaptationStage(platforms=["xiaohongshu", "twitter"]),
        QualityGateStage(quality_threshold=settings.pipeline_quality_threshold),
    ]
    orchestrator = PipelineOrchestrator(stages)

    ctx = PipelineContext(tenant_id=tenant_id, persona_id=persona_id)
    result = _run_async(orchestrator.run(ctx))

    logger.info(
        "Pipeline complete for tenant=%s persona=%s: %d topics, %d errors",
        tenant_id, persona_id, len(result.topics), len(result.errors),
    )

    return {
        "status": "completed" if not result.errors else "completed_with_errors",
        "tenant_id": tenant_id,
        "persona_id": persona_id,
        "topics_discovered": len(result.topics),
        "draft_generated": bool(result.draft_content),
        "error_count": len(result.errors),
    }


@celery_app.task(bind=True, max_retries=2, soft_time_limit=120)
def discover_topics(self: Task, tenant_id: str, persona_id: str) -> dict:
    """Discover topics from external sources."""
    from app.domain import DiscoveryStage, PipelineContext

    stage = DiscoveryStage(sources=["hackernews"])
    ctx = PipelineContext(tenant_id=tenant_id, persona_id=persona_id)
    result = _run_async(stage.execute(ctx))

    return {
        "status": "completed",
        "tenant_id": tenant_id,
        "topics_count": len(result.topics),
        "sources": stage.sources,
    }


@celery_app.task(bind=True, soft_time_limit=120)
def collect_metrics(self: Task, tenant_id: str) -> dict:
    """Collect engagement metrics from all platforms."""
    # TODO: query published content from DB, fetch metrics per platform
    return {"status": "completed", "tenant_id": tenant_id, "publications_checked": 0}


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Celery Beat schedule."""
    from celery.schedules import crontab

    sender.add_periodic_task(
        crontab(hour="*/2"),
        discover_topics.s(),
        name="discover-topics-every-2h",
    )
    sender.add_periodic_task(
        crontab(hour="8,14,20", minute="0"),
        run_content_pipeline.s(),
        name="content-pipeline-3x-daily",
    )
    sender.add_periodic_task(
        crontab(hour="*/6", minute="30"),
        collect_metrics.s(),
        name="collect-metrics-4x-daily",
    )
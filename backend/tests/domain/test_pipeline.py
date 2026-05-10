"""Tests for pipeline orchestration and stages."""

import pytest

from app.domain.pipeline import PipelineContext, PipelineOrchestrator
from app.domain.pipeline.stages import (
    DiscoveryStage,
    GenerationStage,
    QualityGateStage,
    RankingStage,
)


class TestPipelineContext:
    def test_create_context(self):
        ctx = PipelineContext(tenant_id="t1", persona_id="p1")
        assert ctx.tenant_id == "t1"
        assert ctx.persona_id == "p1"
        assert ctx.errors == []
        assert ctx.topics == []

    def test_to_snapshot_roundtrip(self, pipeline_ctx):
        snapshot = pipeline_ctx.to_snapshot()
        assert snapshot["tenant_id"] == "test-tenant-001"
        assert snapshot["selected_topic"] is not None
        assert "errors" in snapshot


class TestPipelineOrchestrator:
    async def test_empty_stages(self, pipeline_ctx):
        orchestrator = PipelineOrchestrator(stages=[])
        result = await orchestrator.run(pipeline_ctx)
        assert result.completed_at is not None

    async def test_single_stage(self, pipeline_ctx):
        stage = QualityGateStage(quality_threshold=0.5)
        orchestrator = PipelineOrchestrator(stages=[stage])
        result = await orchestrator.run(pipeline_ctx)
        assert result.quality_results is not None

    async def test_error_continues(self, pipeline_ctx):
        """Test that a failing stage doesn't abort the pipeline."""
        class FailingStage:
            name = "failing"
            async def execute(self, ctx):
                raise ValueError("Expected failure")

        stage = QualityGateStage()
        orchestrator = PipelineOrchestrator(stages=[FailingStage(), stage])
        result = await orchestrator.run(pipeline_ctx)
        assert len(result.errors) == 1
        assert result.errors[0]["stage"] == "failing"


class TestQualityGateStage:
    async def test_empty_content_issues(self):
        ctx = PipelineContext(tenant_id="t1", persona_id="p1", draft_content="")
        stage = QualityGateStage(quality_threshold=0.7)
        result = await stage.execute(ctx)
        assert len(result.quality_results) >= 1  # too_short

    async def test_good_content_passes(self):
        content = "今天跟大家分享一个关于AI的重要发现！#AI #科技\n" * 5
        ctx = PipelineContext(tenant_id="t1", persona_id="p1", draft_content=content)
        stage = QualityGateStage(quality_threshold=0.5)
        result = await stage.execute(ctx)
        scores = [1.0 + issue.get("score_delta", 0) for issue in result.quality_results]
        final = 1.0 + sum(issue.get("score_delta", 0) for issue in result.quality_results)
        assert final >= 0.5

    async def test_placeholder_detection(self):
        content = "Check out this [TODO] add more content here #AI"
        ctx = PipelineContext(tenant_id="t1", persona_id="p1", draft_content=content)
        stage = QualityGateStage()
        result = await stage.execute(ctx)
        assert any(i["type"] == "placeholder" for i in result.quality_results)

    async def test_no_hashtags_flagged(self):
        content = "This is a post without any hashtags at all."
        ctx = PipelineContext(tenant_id="t1", persona_id="p1", draft_content=content)
        stage = QualityGateStage()
        result = await stage.execute(ctx)
        assert any(i["type"] == "missing_hashtags" for i in result.quality_results)


class TestDiscoveryStage:
    async def test_execute_with_empty_sources(self):
        stage = DiscoveryStage(sources=[])
        ctx = PipelineContext(tenant_id="t1", persona_id="p1")
        result = await stage.execute(ctx)
        assert result.topics == []

    async def test_execute_with_unknown_source(self):
        stage = DiscoveryStage(sources=["nonexistent_source"])
        ctx = PipelineContext(tenant_id="t1", persona_id="p1")
        result = await stage.execute(ctx)
        assert len(result.errors) >= 1
        assert "Unknown source" in result.errors[0]["error"]


class TestRankingStage:
    async def test_empty_topics(self):
        stage = RankingStage()
        ctx = PipelineContext(tenant_id="t1", persona_id="p1")
        result = await stage.execute(ctx)
        assert result.selected_topic is None


class TestDryRunPlatform:
    """Tests for the dry-run publishing platform."""

    async def test_authenticate(self, dry_run_platform):
        assert await dry_run_platform.authenticate() is True

    async def test_publish_creates_file(self, dry_run_platform):
        result = await dry_run_platform.publish("Test content #test", media=None)
        assert result.status == "published"
        assert result.post_id != ""
        assert "output/dry_run" in result.post_id

    async def test_validate_content(self, dry_run_platform):
        valid, _ = await dry_run_platform.validate_content("Valid content")
        assert valid is True

        valid, _ = await dry_run_platform.validate_content("")
        assert valid is False
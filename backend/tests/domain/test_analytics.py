"""Tests for analytics service."""

from datetime import datetime, timedelta

from app.domain.analytics import AnalyticsService, ContentPerformance, WeeklyReport


class TestAnalyticsService:
    async def test_fetch_empty(self):
        svc = AnalyticsService()
        metrics = await svc.fetch_platform_metrics("test", "post-1")
        assert metrics == {}

    async def test_weekly_report_defaults(self):
        svc = AnalyticsService()
        report = await svc.generate_weekly_report("t1")
        assert report.tenant_id == "t1"
        assert report.total_published == 0
        assert report.avg_engagement == 0.0

    async def test_prompt_optimization_empty(self):
        svc = AnalyticsService()
        result = await svc.optimize_prompt_from_performance("p1", [])
        assert "strengths" in result
        assert "weaknesses" in result


class TestContentPerformance:
    def test_defaults(self):
        p = ContentPerformance(content_id="c1", platform="test")
        assert p.likes == 0
        assert p.engagement_rate == 0.0

    def test_custom(self):
        p = ContentPerformance(
            content_id="c1", platform="test",
            likes=100, comments=20, shares=50, views=1000,
            engagement_rate=0.17,
        )
        assert p.engagement_rate == 0.17
        assert p.likes == 100


class TestWeeklyReport:
    def test_defaults(self):
        now = datetime.now()
        report = WeeklyReport(
            tenant_id="t1",
            start_date=now - timedelta(days=7),
            end_date=now,
        )
        assert report.total_published == 0
        assert report.insights == []
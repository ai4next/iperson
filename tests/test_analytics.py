from __future__ import annotations

import os
from pathlib import Path

from iperson.analytics.engine import AnalyticsEngine
from iperson.storage import init_db
from iperson.storage.db import get_connection


class TestAnalyticsEngine:
    _db_path: str = "/tmp/test_analytics.db"

    def setup_method(self) -> None:
        # Remove any leftover DB from previous runs
        Path(self._db_path).unlink(missing_ok=True)
        os.environ["IPERSON_DB_PATH"] = self._db_path
        init_db()

    def teardown_method(self) -> None:
        del os.environ["IPERSON_DB_PATH"]

    def _insert_content(self, content_id: str) -> None:
        """Helper to insert a content record to satisfy FK constraint."""
        conn = get_connection()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO contents (id, topic, title, content_type) VALUES (?, ?, ?, ?)",
                (content_id, "test", "Test Content", "article"),
            )
            conn.commit()
        finally:
            conn.close()

    def test_collect_and_get_metrics(self) -> None:
        self._insert_content("test-001")
        engine = AnalyticsEngine()
        engine.collect_metrics(
            "test-001", "xiaohongshu", views=100, likes=20, shares=5, comments=3
        )
        metrics = engine.get_metrics("test-001")
        assert len(metrics) >= 1
        assert metrics[0]["views"] == 100

    def test_get_summary(self) -> None:
        self._insert_content("test-002")
        engine = AnalyticsEngine()
        engine.collect_metrics("test-002", "xiaohongshu", views=100, likes=20)
        engine.collect_metrics("test-002", "wechat", views=200, likes=30)
        summary = engine.get_summary("test-002")
        assert summary["total_views"] == 300
        assert summary["total_likes"] == 50
        assert summary["platforms"] == 2

    def test_empty_content(self) -> None:
        engine = AnalyticsEngine()
        summary = engine.get_summary("nonexistent")
        assert summary["total_views"] == 0
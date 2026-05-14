from __future__ import annotations

import os
from pathlib import Path

from iperson.storage import init_db
from iperson.storage.db import get_connection
from iperson.topics.engine import TopicSuggestionEngine


class TestTopicSuggestionEngine:
    _db_path: str = "/tmp/test_topics.db"

    def setup_method(self) -> None:
        Path(self._db_path).unlink(missing_ok=True)
        os.environ["IPERSON_DB_PATH"] = self._db_path
        init_db()
        self._seed_data()

    def teardown_method(self) -> None:
        del os.environ["IPERSON_DB_PATH"]

    def _seed_data(self) -> None:
        """Insert test data covering both KB and analytics sources."""
        conn = get_connection()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO kb_docs (id, title, content) VALUES (?, ?, ?)",
                ("kb-1", "Python 编程入门", "Python 是一种高级编程语言，适合初学者。"),
            )
            conn.execute(
                "INSERT OR IGNORE INTO kb_docs (id, title, content) VALUES (?, ?, ?)",
                ("kb-2", "机器学习基础", "机器学习是人工智能的重要分支。"),
            )
            conn.execute(
                "INSERT OR IGNORE INTO contents (id, topic, title, content_type) VALUES (?, ?, ?, ?)",
                ("content-1", "AI 发展趋势", "2026 AI Trends", "article"),
            )
            conn.execute(
                "INSERT OR IGNORE INTO content_metrics (id, content_id, platform, views, likes) VALUES (?, ?, ?, ?, ?)",
                ("m-1", "content-1", "xiaohongshu", 1500, 200),
            )
            conn.commit()
        finally:
            conn.close()

    def test_suggest_all_returns_list(self) -> None:
        engine = TopicSuggestionEngine()
        suggestions = engine.suggest_all(top_n=3)
        assert isinstance(suggestions, list)

    def test_suggestions_have_required_fields(self) -> None:
        engine = TopicSuggestionEngine()
        suggestions = engine.suggest_all(top_n=3)
        for s in suggestions:
            assert s.topic
            assert s.source in ("kb", "trending", "analytics")
            assert 0.0 <= s.score <= 1.0
            assert s.reason

    def test_suggest_all_returns_nonempty(self) -> None:
        engine = TopicSuggestionEngine()
        suggestions = engine.suggest_all(top_n=3)
        assert len(suggestions) > 0, "Should return at least one suggestion from seeded data"

    def test_suggest_from_kb(self) -> None:
        engine = TopicSuggestionEngine()
        suggestions = engine.suggest_from_kb(top_n=5)
        assert len(suggestions) > 0
        assert all(s.source == "kb" for s in suggestions)

    def test_suggest_from_analytics(self) -> None:
        engine = TopicSuggestionEngine()
        suggestions = engine.suggest_from_analytics(top_n=5)
        assert len(suggestions) > 0
        assert all(s.source == "analytics" for s in suggestions)
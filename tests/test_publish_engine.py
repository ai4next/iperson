from __future__ import annotations

import pytest
from iperson.publish.engine import PublicationStatus, PublishEngine


class TestPublicationStatus:
    def test_status_transitions(self) -> None:
        s = PublicationStatus()
        assert s.current == "draft"
        assert s.can_transition_to("queued") is True
        assert s.can_transition_to("published") is False

    def test_status_transition(self) -> None:
        s = PublicationStatus()
        s.transition_to("queued")
        assert s.current == "queued"
        s.transition_to("publishing")
        assert s.current == "publishing"
        s.transition_to("published")
        assert s.current == "published"

    def test_invalid_transition_raises(self) -> None:
        s = PublicationStatus()
        with pytest.raises(
            ValueError, match="Cannot transition from draft to published"
        ):
            s.transition_to("published")


class TestPublishEngine:
    def test_create_publication(self) -> None:
        from iperson.storage import init_db
        from iperson.storage.db import get_connection
        init_db()
        # Insert a content record to satisfy foreign key
        conn = get_connection()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO contents (id, topic) VALUES (?, ?)",
                ("content_123", "test"),
            )
            conn.commit()
        finally:
            conn.close()
        engine = PublishEngine()
        pub = engine.create("content_123", "xiaohongshu")
        assert pub["content_id"] == "content_123"
        assert pub["platform"] == "xiaohongshu"
        assert pub["status"] == "draft"

    def test_list_publications_empty(self) -> None:
        from iperson.storage import init_db
        init_db()
        engine = PublishEngine()
        pubs = engine.list_publications()
        assert isinstance(pubs, list)
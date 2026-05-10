"""Tests for publish hub — registry and platform adapters."""

from app.domain.publish import DryRunPlatform, PlatformRegistry, PublishResult


class TestPlatformRegistry:
    def test_dry_run_registered(self):
        assert "dry_run" in PlatformRegistry._platforms

    def test_get_registered_platform(self):
        klass = PlatformRegistry.get("dry_run")
        assert klass == DryRunPlatform

    def test_get_unknown_platform(self):
        try:
            PlatformRegistry.get("nonexistent")
            assert False, "Should have raised KeyError"
        except KeyError:
            pass

    def test_list_available(self):
        platforms = PlatformRegistry.list_available()
        assert "dry_run" in platforms


class TestPublishResult:
    def test_default_values(self):
        result = PublishResult()
        assert result.post_id == ""
        assert result.status == "pending"
        assert result.error == ""

    def test_custom_values(self):
        result = PublishResult(
            post_id="post-123",
            url="https://example.com/post/123",
            status="published",
            metadata={"likes": 0},
        )
        assert result.post_id == "post-123"
        assert result.status == "published"
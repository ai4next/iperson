from __future__ import annotations

from iperson.tuning.engine import StyleTuningEngine


class TestStyleTuningEngine:
    def test_analyze_banned_patterns_returns_list(self) -> None:
        engine = StyleTuningEngine()
        suggestions = engine.analyze_banned_patterns("default")
        assert isinstance(suggestions, list)

    def test_tuning_suggestion_has_required_fields(self) -> None:
        from iperson.tuning.engine import TuningSuggestion
        s = TuningSuggestion(
            dimension="test", current_value="a", suggested_value="b",
            reason="test", confidence=0.5,
        )
        assert s.dimension == "test"
        assert 0.0 <= s.confidence <= 1.0
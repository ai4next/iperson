from __future__ import annotations

import pytest

from iperson.pipeline.pipeline import validate_pipeline, PipelineValidationError


class TestRecipeValidation:
    def test_valid_recipe_no_errors(self) -> None:
        data = {
            "name": "test",
            "stages": [
                {"plugin": "research.kb_retrieve", "config": {"top_k": 5}},
                {"plugin": "generation.article"},
            ],
        }
        errors = validate_pipeline(data)
        assert errors == []

    def test_missing_name(self) -> None:
        data = {"stages": [{"plugin": "test"}]}
        errors = validate_pipeline(data)
        assert any("name" in e for e in errors)

    def test_missing_stages(self) -> None:
        data = {"name": "test"}
        errors = validate_pipeline(data)
        assert any("stages" in e for e in errors)

    def test_empty_stages(self) -> None:
        data = {"name": "test", "stages": []}
        errors = validate_pipeline(data)
        assert any("empty" in e for e in errors)

    def test_stage_missing_plugin(self) -> None:
        data = {"name": "test", "stages": [{"config": {}}]}
        errors = validate_pipeline(data)
        assert any("plugin" in e for e in errors)

    def test_invalid_stages_type(self) -> None:
        data = {"name": "test", "stages": "not_a_list"}
        errors = validate_pipeline(data)
        assert errors
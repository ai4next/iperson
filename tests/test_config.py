from __future__ import annotations

import pytest

from iperson.pipeline.pipeline import validate_pipeline, PipelineValidationError


class TestRecipeValidation:
    def test_valid_recipe_no_errors(self) -> None:
        data = {
            "name": "test",
            "nodes": [
                {"id": "research", "node": "research.kb_retrieve", "config": {"top_k": 5}},
                {"id": "generate", "node": "generation.article"},
            ],
        }
        errors = validate_pipeline(data)
        assert errors == []

    def test_missing_name(self) -> None:
        data = {"nodes": [{"id": "step", "node": "test"}]}
        errors = validate_pipeline(data)
        assert any("name" in e for e in errors)

    def test_missing_stages(self) -> None:
        data = {"name": "test"}
        errors = validate_pipeline(data)
        assert any("nodes" in e for e in errors)

    def test_empty_stages(self) -> None:
        data = {"name": "test", "nodes": []}
        errors = validate_pipeline(data)
        assert any("empty" in e for e in errors)

    def test_stage_missing_plugin(self) -> None:
        data = {"name": "test", "nodes": [{"id": "step", "config": {}}]}
        errors = validate_pipeline(data)
        assert any("node" in e for e in errors)

    def test_invalid_stages_type(self) -> None:
        data = {"name": "test", "nodes": "not_a_list"}
        errors = validate_pipeline(data)
        assert errors
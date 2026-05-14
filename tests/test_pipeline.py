from __future__ import annotations

from typing import Any

import pytest

from iperson.pipeline.context import PipelineContext
from iperson.pipeline.orchestrator import PipelineOrchestrator
from iperson.pipeline.plugin import StagePlugin
from iperson.pipeline.recipe import load_recipe_from_yaml
from iperson.pipeline.registry import PluginRegistry

SAMPLE_RECIPE = """
name: test-recipe
description: "Test recipe"
stages:
  - plugin: test.stage_one
    config:
      key: value
  - plugin: test.stage_two
"""


class StageOne(StagePlugin):
    plugin_id = "test.stage_one"
    name = "Stage One"
    description = "First test stage"
    category = "generation"
    version = "1.0.0"

    async def execute(
        self, ctx: PipelineContext, config: dict[str, Any] | None = None
    ) -> PipelineContext:
        ctx.data["stage_one_done"] = True
        return ctx


class StageTwo(StagePlugin):
    plugin_id = "test.stage_two"
    name = "Stage Two"
    description = "Second test stage"
    category = "quality"
    version = "1.0.0"

    async def execute(
        self, ctx: PipelineContext, config: dict[str, Any] | None = None
    ) -> PipelineContext:
        ctx.data["stage_two_done"] = True
        return ctx


class FailingStage(StagePlugin):
    plugin_id = "test.failing"
    name = "Failing Stage"
    description = "Stage that always fails"
    category = "quality"
    version = "1.0.0"

    async def execute(
        self, ctx: PipelineContext, config: dict[str, Any] | None = None
    ) -> PipelineContext:
        msg = "Intentional failure"
        raise RuntimeError(msg)


class TestPipelineContext:
    def test_create_context(self) -> None:
        ctx = PipelineContext(persona_id="persona-1", topic="Python")
        assert ctx.persona_id == "persona-1"
        assert ctx.topic == "Python"
        assert ctx.recipe_name == "quick"
        assert ctx.status == "running"
        assert ctx.content_id is None
        assert ctx.kb_chunks == []
        assert ctx.kb_context == ""
        assert ctx.generated_content == ""
        assert ctx.humanized_content == ""
        assert ctx.audit_result == {}
        assert ctx.publish_results == []
        assert ctx.platform_contents == {}
        assert ctx.data == {}
        assert ctx.errors == []
        assert ctx.completed_at is None
        assert isinstance(ctx.id, str) and len(ctx.id) > 0

    def test_create_context_with_content_id(self) -> None:
        ctx = PipelineContext(
            persona_id="persona-2",
            topic="Go",
            recipe_name="full",
            content_id="content-123",
        )
        assert ctx.persona_id == "persona-2"
        assert ctx.topic == "Go"
        assert ctx.recipe_name == "full"
        assert ctx.content_id == "content-123"

    def test_snapshot_roundtrip(self) -> None:
        ctx = PipelineContext(persona_id="persona-1", topic="Python")
        ctx.kb_context = "Some KB context"
        ctx.generated_content = "Generated draft"
        ctx.humanized_content = "Humanized draft"
        ctx.data["custom"] = {"nested": True}
        ctx.status = "completed"
        ctx.errors.append({"stage": "test", "error": "something"})

        snapshot = ctx.to_snapshot()
        restored = PipelineContext.from_snapshot(snapshot)

        assert restored.id == ctx.id
        assert restored.persona_id == ctx.persona_id
        assert restored.topic == ctx.topic
        assert restored.recipe_name == ctx.recipe_name
        assert restored.content_id == ctx.content_id
        assert restored.status == ctx.status
        assert restored.kb_context == ctx.kb_context
        assert restored.generated_content == ctx.generated_content
        assert restored.humanized_content == ctx.humanized_content
        assert restored.data == ctx.data
        assert restored.errors == ctx.errors

    def test_snapshot_independence(self) -> None:
        """Verify that snapshot data is deep-copied and independent."""
        ctx = PipelineContext(persona_id="p1", topic="T")
        ctx.data["list"] = [1, 2, 3]
        snapshot = ctx.to_snapshot()
        # Modify original after snapshot
        ctx.data["list"].append(4)
        # Snapshot should be unchanged
        assert snapshot["data"]["list"] == [1, 2, 3]

    def test_from_snapshot_empty(self) -> None:
        """from_snapshot with empty dict should use defaults."""
        restored = PipelineContext.from_snapshot({})
        assert restored.persona_id == ""
        assert restored.topic == ""
        assert restored.recipe_name == "quick"
        assert restored.content_id is None
        assert restored.status == "running"


class TestPluginRegistry:
    def test_register_and_get(self) -> None:
        registry = PluginRegistry()
        registry.register(StageOne)
        cls = registry.get("test.stage_one")
        assert cls is StageOne
        assert cls.plugin_id == "test.stage_one"
        assert cls.name == "Stage One"

    def test_get_unknown_plugin(self) -> None:
        registry = PluginRegistry()
        with pytest.raises(KeyError) as excinfo:
            registry.get("nonexistent.plugin")
        msg = str(excinfo.value)
        assert "nonexistent.plugin" in msg
        assert "none registered" in msg

    def test_get_unknown_plugin_with_available(self) -> None:
        registry = PluginRegistry()
        registry.register(StageOne)
        with pytest.raises(KeyError) as excinfo:
            registry.get("nonexistent.plugin")
        msg = str(excinfo.value)
        assert "nonexistent.plugin" in msg
        assert "test.stage_one" in msg

    def test_list_plugins(self) -> None:
        registry = PluginRegistry()
        registry.register(StageOne)
        registry.register(StageTwo)

        plugins = registry.list_plugins()
        assert len(plugins) == 2

        ids = [p["plugin_id"] for p in plugins]
        assert "test.stage_one" in ids
        assert "test.stage_two" in ids

        one = next(p for p in plugins if p["plugin_id"] == "test.stage_one")
        assert one["name"] == "Stage One"
        assert one["category"] == "generation"
        assert one["version"] == "1.0.0"

    def test_list_plugins_empty(self) -> None:
        registry = PluginRegistry()
        assert registry.list_plugins() == []

    def test_has(self) -> None:
        registry = PluginRegistry()
        assert not registry.has("test.stage_one")
        registry.register(StageOne)
        assert registry.has("test.stage_one")
        assert not registry.has("test.stage_two")

    def test_register_empty_id_raises(self) -> None:
        class BadPlugin(StagePlugin):
            plugin_id = ""

            async def execute(self, ctx, config=None):
                return ctx

        registry = PluginRegistry()
        with pytest.raises(ValueError, match="non-empty plugin_id"):
            registry.register(BadPlugin)

    def test_register_duplicate_overwrites(self) -> None:
        registry = PluginRegistry()
        registry.register(StageOne)
        registry.register(StageOne)  # Should not raise
        assert registry.has("test.stage_one")


class TestRecipe:
    def test_load_recipe_from_yaml(self) -> None:
        recipe = load_recipe_from_yaml(SAMPLE_RECIPE)
        assert recipe["name"] == "test-recipe"
        assert recipe["description"] == "Test recipe"
        assert len(recipe["stages"]) == 2

        stage0 = recipe["stages"][0]
        assert stage0["plugin"] == "test.stage_one"
        assert stage0["config"] == {"key": "value"}

        stage1 = recipe["stages"][1]
        assert stage1["plugin"] == "test.stage_two"

    def test_load_recipe_without_config(self) -> None:
        yaml_str = """
name: minimal
stages:
  - plugin: my.plugin
"""
        recipe = load_recipe_from_yaml(yaml_str)
        assert recipe["stages"][0]["config"] == {}

    def test_load_recipe_no_stages(self) -> None:
        yaml_str = """
name: empty-recipe
description: "No stages"
"""
        recipe = load_recipe_from_yaml(yaml_str)
        assert recipe["name"] == "empty-recipe"
        assert recipe["stages"] == []

    def test_load_recipe_missing_name(self) -> None:
        yaml_str = """
stages:
  - plugin: test
"""
        with pytest.raises(ValueError, match="name"):
            load_recipe_from_yaml(yaml_str)

    def test_load_recipe_missing_plugin_field(self) -> None:
        yaml_str = """
name: bad
stages:
  - config:
      foo: bar
"""
        with pytest.raises(ValueError, match="plugin"):
            load_recipe_from_yaml(yaml_str)

    def test_load_recipe_not_a_mapping(self) -> None:
        with pytest.raises(ValueError, match="mapping"):
            load_recipe_from_yaml("hello")

    def test_load_recipe_from_file_not_found(self) -> None:
        from iperson.pipeline.recipe import load_recipe_from_file

        with pytest.raises(FileNotFoundError, match="not found"):
            load_recipe_from_file("/nonexistent/recipe.yaml")


class TestOrchestrator:
    @pytest.mark.asyncio
    async def test_orchestrator_run_two_stages(self) -> None:
        registry = PluginRegistry()
        registry.register(StageOne)
        registry.register(StageTwo)

        recipe = load_recipe_from_yaml(SAMPLE_RECIPE)
        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(persona_id="p1", topic="Python")

        result = await orchestrator.run(ctx, recipe)

        assert result.data.get("stage_one_done") is True
        assert result.data.get("stage_two_done") is True
        assert result.status == "completed"
        assert result.completed_at is not None
        assert "_timing_test.stage_one" in result.data
        assert "_timing_test.stage_two" in result.data

    @pytest.mark.asyncio
    async def test_orchestrator_error_handling(self) -> None:
        registry = PluginRegistry()
        registry.register(StageOne)
        registry.register(FailingStage)
        registry.register(StageTwo)

        recipe = load_recipe_from_yaml(SAMPLE_RECIPE)
        # Replace stage_two with failing stage
        recipe["stages"] = [
            {"plugin": "test.stage_one", "config": {}},
            {"plugin": "test.failing", "config": {}},
            {"plugin": "test.stage_two", "config": {}},
        ]

        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(persona_id="p1", topic="Python")

        result = await orchestrator.run(ctx, recipe)

        # Stage one should have run
        assert result.data.get("stage_one_done") is True
        # Stage two should also have run (error doesn't stop pipeline)
        assert result.data.get("stage_two_done") is True
        # error should be recorded
        assert len(result.errors) >= 1
        assert result.errors[0]["stage"] == "test.failing"
        assert "Intentional failure" in result.errors[0]["error"]
        assert result.status == "completed_with_errors"

    @pytest.mark.asyncio
    async def test_orchestrator_unknown_plugin(self) -> None:
        registry = PluginRegistry()
        registry.register(StageOne)

        recipe = load_recipe_from_yaml(
            """
name: unknown-plugin
stages:
  - plugin: test.stage_one
  - plugin: nonexistent.plugin
  - plugin: test.stage_two
"""
        )

        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(persona_id="p1", topic="Python")

        result = await orchestrator.run(ctx, recipe)

        # Pre-validation returns immediately on first unknown plugin
        assert result.data.get("stage_one_done") is not True
        assert len(result.errors) == 1
        assert result.errors[0].error_code == "PLUGIN_NOT_FOUND"
        assert result.errors[0].stage == "nonexistent.plugin"
        assert "Unknown plugin" in result.errors[0].message

    @pytest.mark.asyncio
    async def test_orchestrator_retry_success(self) -> None:
        """Stage that fails once then succeeds with retry."""

        class RetryStage(StagePlugin):
            plugin_id = "test.retry"
            name = "Retry Stage"
            description = "Fails first time then succeeds"
            category = "quality"

            def __init__(self) -> None:
                super().__init__()
                self._attempts = 0

            async def execute(
                self, ctx: PipelineContext, config: dict[str, Any] | None = None
            ) -> PipelineContext:
                self._attempts += 1
                if self._attempts == 1:
                    msg = "First attempt failure"
                    raise RuntimeError(msg)
                ctx.data["retry_done"] = True
                return ctx

        registry = PluginRegistry()
        registry.register(RetryStage)

        recipe = load_recipe_from_yaml(
            """
name: retry-test
stages:
  - plugin: test.retry
    config:
      max_retries: 2
"""
        )

        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(persona_id="p1", topic="Python")

        result = await orchestrator.run(ctx, recipe)

        assert result.data.get("retry_done") is True
        # When retry succeeds, no errors are recorded
        assert len(result.errors) == 0
        assert result.status == "completed"

    @pytest.mark.asyncio
    async def test_orchestrator_retry_exhausted(self) -> None:
        registry = PluginRegistry()
        registry.register(FailingStage)

        recipe = load_recipe_from_yaml(
            """
name: retry-fail
stages:
  - plugin: test.failing
    config:
      max_retries: 1
"""
        )

        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(persona_id="p1", topic="Python")

        result = await orchestrator.run(ctx, recipe)

        assert len(result.errors) >= 1
        # With max_retries=1, we should have 1 retry attempt + original = 2 total attempts
        assert result.errors[-1]["attempts"] == 2
        assert result.errors[-1]["stage"] == "test.failing"
        assert result.status == "completed_with_errors"

    @pytest.mark.asyncio
    async def test_orchestrator_empty_stages(self) -> None:
        registry = PluginRegistry()
        recipe = load_recipe_from_yaml(
            """
name: empty
stages: []
"""
        )
        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(persona_id="p1", topic="Python")
        result = await orchestrator.run(ctx, recipe)
        assert result.status == "completed"
        assert result.completed_at is not None


class TestPluginDefaults:
    def test_plugin_default_config(self) -> None:
        assert StageOne.default_config == {}
        assert StageOne.config_schema == {}
        assert StageOne.plugin_id == "test.stage_one"
        assert StageOne.category == "generation"

    def test_plugin_version_default(self) -> None:
        assert StageOne.version == "1.0.0"

    def test_plugin_tags_default(self) -> None:
        assert StageOne.tags == []


from iperson.pipeline.errors import PipelineError


def test_pipeline_error_defaults() -> None:
    err = PipelineError(error_code="TEST", stage="test", message="test error")
    assert err.error_code == "TEST"
    assert err.recoverable is False
    assert err.timestamp is not None


def test_pipeline_error_recoverable() -> None:
    err = PipelineError(error_code="TEST", stage="test", message="recoverable", recoverable=True)
    assert err.recoverable is True
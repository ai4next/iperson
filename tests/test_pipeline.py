from __future__ import annotations

from typing import Any

import pytest

from iperson.pipeline.context import PipelineContext
from iperson.pipeline.orchestrator import PipelineOrchestrator
from iperson.pipeline.plugin import StagePlugin
from iperson.pipeline.pipeline import load_pipeline_from_yaml
from iperson.pipeline.registry import PluginRegistry

SAMPLE_RECIPE = """
name: test-recipe
description: "Test recipe"
nodes:
  - id: stage_one
    node: test.stage_one
    config:
      key: value
  - id: stage_two
    node: test.stage_two
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
        ctx = PipelineContext(persona_name="persona-1", topic="Python")
        assert ctx.persona_name == "persona-1"
        assert ctx.topic == "Python"
        assert ctx.pipeline_name == "quick"
        assert ctx.status == "running"
        assert ctx.content_id is None
        assert ctx.kb_chunks == []
        assert ctx.kb_context == ""
        assert ctx.generated_content == ""
        assert ctx.publish_results == []
        assert ctx.platform_contents == {}
        assert ctx.data == {}
        assert ctx.errors == []
        assert ctx.completed_at is None
        assert isinstance(ctx.id, str) and len(ctx.id) > 0

    def test_create_context_with_content_id(self) -> None:
        ctx = PipelineContext(
            persona_name="persona-2",
            topic="Go",
            pipeline_name="full",
            content_id="content-123",
        )
        assert ctx.persona_name == "persona-2"
        assert ctx.topic == "Go"
        assert ctx.pipeline_name == "full"
        assert ctx.content_id == "content-123"

    def test_snapshot_roundtrip(self) -> None:
        ctx = PipelineContext(persona_name="persona-1", topic="Python")
        ctx.kb_context = "Some KB context"
        ctx.generated_content = "Generated draft"
        ctx.data["custom"] = {"nested": True}
        ctx.status = "completed"
        ctx.errors.append({"stage": "test", "error": "something"})

        snapshot = ctx.to_snapshot()
        restored = PipelineContext.from_snapshot(snapshot)

        assert restored.id == ctx.id
        assert restored.persona_name == ctx.persona_name
        assert restored.topic == ctx.topic
        assert restored.pipeline_name == ctx.pipeline_name
        assert restored.content_id == ctx.content_id
        assert restored.status == ctx.status
        assert restored.kb_context == ctx.kb_context
        assert restored.generated_content == ctx.generated_content
        assert restored.data == ctx.data
        assert restored.errors == ctx.errors

    def test_snapshot_independence(self) -> None:
        """Verify that snapshot data is deep-copied and independent."""
        ctx = PipelineContext(persona_name="p1", topic="T")
        ctx.data["list"] = [1, 2, 3]
        snapshot = ctx.to_snapshot()
        # Modify original after snapshot
        ctx.data["list"].append(4)
        # Snapshot should be unchanged
        assert snapshot["data"]["list"] == [1, 2, 3]

    def test_from_snapshot_empty(self) -> None:
        """from_snapshot with empty dict should use defaults."""
        restored = PipelineContext.from_snapshot({})
        assert restored.persona_name == ""
        assert restored.topic == ""
        assert restored.pipeline_name == "quick"
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
    def test_load_pipeline_from_yaml(self) -> None:
        recipe = load_pipeline_from_yaml(SAMPLE_RECIPE)
        assert recipe["name"] == "test-recipe"
        assert recipe["description"] == "Test recipe"
        assert len(recipe["nodes"]) == 2

        node0 = recipe["nodes"][0]
        assert node0["node"] == "test.stage_one"
        assert node0["config"] == {"key": "value"}

        node1 = recipe["nodes"][1]
        assert node1["node"] == "test.stage_two"

    def test_load_recipe_without_config(self) -> None:
        yaml_str = """
name: minimal
nodes:
  - id: step
    node: my.plugin
"""
        recipe = load_pipeline_from_yaml(yaml_str)
        assert recipe["nodes"][0]["config"] == {}

    def test_load_recipe_no_stages(self) -> None:
        yaml_str = """
name: empty-recipe
description: "No stages"
"""
        recipe = load_pipeline_from_yaml(yaml_str)
        assert recipe["name"] == "empty-recipe"
        assert recipe["nodes"] == []

    def test_load_recipe_missing_name(self) -> None:
        yaml_str = """
nodes:
  - id: step
    node: test
"""
        with pytest.raises(ValueError, match="name"):
            load_pipeline_from_yaml(yaml_str)

    def test_load_recipe_missing_plugin_field(self) -> None:
        yaml_str = """
name: bad
nodes:
  - id: step
    config:
      foo: bar
"""
        with pytest.raises(ValueError, match="node"):
            load_pipeline_from_yaml(yaml_str)

    def test_load_recipe_not_a_mapping(self) -> None:
        with pytest.raises(ValueError, match="mapping"):
            load_pipeline_from_yaml("hello")

    def test_load_recipe_from_file_not_found(self) -> None:
        from iperson.pipeline.pipeline import load_pipeline_from_file

        with pytest.raises(FileNotFoundError, match="not found"):
            load_pipeline_from_file("/nonexistent/recipe.yaml")


class TestOrchestrator:
    @pytest.mark.asyncio
    async def test_orchestrator_run_two_stages(self) -> None:
        registry = PluginRegistry()
        registry.register(StageOne)
        registry.register(StageTwo)

        recipe = load_pipeline_from_yaml(SAMPLE_RECIPE)
        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(persona_name="p1", topic="Python")

        result = await orchestrator.run(ctx, recipe)

        assert result.data.get("stage_one_done") is True
        assert result.data.get("stage_two_done") is True
        assert result.status == "completed"
        assert result.completed_at is not None

    @pytest.mark.asyncio
    async def test_orchestrator_error_handling(self) -> None:
        registry = PluginRegistry()
        registry.register(StageOne)
        registry.register(FailingStage)
        registry.register(StageTwo)

        recipe = load_pipeline_from_yaml(SAMPLE_RECIPE)
        # Replace stage_two with failing stage
        recipe["nodes"] = [
            {"id": "stage_one", "node": "test.stage_one", "config": {}},
            {"id": "failing", "node": "test.failing", "config": {}},
            {"id": "stage_two", "node": "test.stage_two", "config": {}},
        ]

        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(persona_name="p1", topic="Python")

        with pytest.raises(RuntimeError, match="Intentional failure"):
            await orchestrator.run(ctx, recipe)

    @pytest.mark.asyncio
    async def test_orchestrator_unknown_plugin(self) -> None:
        registry = PluginRegistry()
        registry.register(StageOne)

        recipe = load_pipeline_from_yaml(
            """
name: unknown-plugin
nodes:
  - id: stage_one
    node: test.stage_one
  - id: unknown
    node: nonexistent.plugin
  - id: stage_two
    node: test.stage_two
"""
        )

        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(persona_name="p1", topic="Python")

        with pytest.raises(KeyError, match="nonexistent.plugin"):
            await orchestrator.run(ctx, recipe)

    @pytest.mark.asyncio
    async def test_orchestrator_retry_success(self) -> None:
        """Stage that fails once would have been retried in old orchestrator."""

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

        recipe = load_pipeline_from_yaml(
            """
name: retry-test
nodes:
  - id: retry
    node: test.retry
    config:
      max_retries: 2
"""
        )

        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(persona_name="p1", topic="Python")

        with pytest.raises(RuntimeError, match="First attempt failure"):
            await orchestrator.run(ctx, recipe)

    @pytest.mark.asyncio
    async def test_orchestrator_retry_exhausted(self) -> None:
        registry = PluginRegistry()
        registry.register(FailingStage)

        recipe = load_pipeline_from_yaml(
            """
name: retry-fail
nodes:
  - id: failing
    node: test.failing
    config:
      max_retries: 1
"""
        )

        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(persona_name="p1", topic="Python")

        with pytest.raises(RuntimeError, match="Intentional failure"):
            await orchestrator.run(ctx, recipe)

    @pytest.mark.asyncio
    async def test_orchestrator_empty_stages(self) -> None:
        registry = PluginRegistry()
        recipe = load_pipeline_from_yaml(
            """
name: empty
nodes: []
"""
        )
        orchestrator = PipelineOrchestrator(registry)
        ctx = PipelineContext(persona_name="p1", topic="Python")
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


@pytest.mark.asyncio
async def test_pipeline_unknown_plugin_pre_validation() -> None:
    """Unknown plugin should raise KeyError."""
    registry = PluginRegistry()
    orchestrator = PipelineOrchestrator(registry)
    ctx = PipelineContext(topic="test")
    recipe = {"name": "test", "nodes": [{"id": "step", "node": "nonexistent.plugin"}]}
    with pytest.raises(KeyError, match="nonexistent.plugin"):
        await orchestrator.run(ctx, recipe)


@pytest.mark.asyncio
async def test_pipeline_on_error_skip() -> None:
    """on_error=skip is not supported in LangGraph pipeline; exception propagates."""
    registry = PluginRegistry()

    class FailingPlugin(StagePlugin):
        plugin_id = "test.fail"

        async def execute(self, ctx: PipelineContext, config: dict) -> PipelineContext:
            raise RuntimeError("stage failed")

    registry.register(FailingPlugin)

    class PassingPlugin(StagePlugin):
        plugin_id = "test.pass"

        async def execute(self, ctx: PipelineContext, config: dict) -> PipelineContext:
            return ctx

    registry.register(PassingPlugin)

    orchestrator = PipelineOrchestrator(registry)
    ctx = PipelineContext(topic="test")
    recipe = {
        "name": "test",
        "nodes": [
            {"id": "fail", "node": "test.fail", "config": {"on_error": "skip"}},
            {"id": "pass", "node": "test.pass"},
        ],
    }
    with pytest.raises(RuntimeError, match="stage failed"):
        await orchestrator.run(ctx, recipe)


@pytest.mark.asyncio
async def test_pipeline_on_error_abort() -> None:
    """on_error=abort is not supported in LangGraph pipeline; exception propagates."""
    registry = PluginRegistry()

    class FailStage(StagePlugin):
        plugin_id = "test.abort_fail"

        async def execute(self, ctx: PipelineContext, config: dict) -> PipelineContext:
            raise RuntimeError("abort")

    registry.register(FailStage)

    orchestrator = PipelineOrchestrator(registry)
    ctx = PipelineContext(topic="test")
    recipe = {
        "name": "test",
        "nodes": [
            {"id": "fail", "node": "test.abort_fail", "config": {"on_error": "abort"}},
        ],
    }
    with pytest.raises(RuntimeError, match="abort"):
        await orchestrator.run(ctx, recipe)


class TestPipelineHooks:
    @pytest.mark.asyncio
    async def test_pipeline_runs_hooks_before_and_after_stage(self) -> None:
        from iperson.pipeline.hook import BaseHook, HookContext, HookRegistry

        registry = PluginRegistry()
        hook_registry = HookRegistry()

        class SimplePlugin(StagePlugin):
            plugin_id = "test.simple"
            name = "Simple"

            async def execute(
                self, ctx: PipelineContext, config: dict[str, Any] | None = None
            ) -> PipelineContext:
                ctx.data["stage_ran"] = True
                return ctx

        registry.register(SimplePlugin)

        class BeforeHook(BaseHook):
            hook_id = "test.before"
            hook_point = "before.test.simple"
            name = "Before"

            async def execute(self, ctx: HookContext) -> HookContext:
                ctx.pipeline_ctx.data["before_ran"] = True
                return ctx

        class AfterHook(BaseHook):
            hook_id = "test.after"
            hook_point = "after.test.simple"
            name = "After"

            async def execute(self, ctx: HookContext) -> HookContext:
                ctx.pipeline_ctx.data["after_ran"] = True
                return ctx

        hook_registry.register(BeforeHook)
        hook_registry.register(AfterHook)

        orch = PipelineOrchestrator(registry, hook_registry=hook_registry)
        ctx = PipelineContext(topic="test")
        recipe = {"name": "test", "nodes": [{"id": "simple", "node": "test.simple", "config": {}}]}
        result = await orch.run(ctx, recipe)
        assert result.data.get("before_ran") is True
        assert result.data.get("stage_ran") is True
        assert result.data.get("after_ran") is True


class TestRecipeHooks:
    def test_recipe_can_include_hooks(self) -> None:
        from iperson.pipeline.pipeline import load_pipeline_from_file
        import os

        recipe_path = os.path.join(
            os.path.dirname(__file__), "..", "pipelines", "default.yaml"
        )
        recipe = load_pipeline_from_file(recipe_path)
        nodes = recipe.get("nodes", [])
        gen_node = next(
            (n for n in nodes if n["node"] == "generation.article"), None
        )
        assert gen_node is not None
        assert "hooks" not in gen_node or isinstance(gen_node["hooks"], dict)
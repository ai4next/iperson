from __future__ import annotations

import pytest
from iperson.pipeline.loader import FilePluginLoader, PipPluginLoader


class TestFilePluginLoader:
    def test_load_from_nonexistent_dir_returns_empty(self, tmp_path) -> None:
        loader = FilePluginLoader(tmp_path / "nonexistent")
        plugins = loader.load_plugins()
        assert plugins == []

    def test_load_from_empty_dir_returns_empty(self, tmp_path) -> None:
        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()
        loader = FilePluginLoader(plugin_dir)
        plugins = loader.load_plugins()
        assert plugins == []
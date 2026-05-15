from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

from iperson.pipeline.hook import BaseHook
from iperson.pipeline.plugin import StagePlugin


class FilePluginLoader:
    """Load plugins and hooks from a directory of .py files."""

    def __init__(self, plugin_dir: Path) -> None:
        self.plugin_dir = plugin_dir

    def load_plugins(self) -> list[type[StagePlugin]]:
        if not self.plugin_dir.exists():
            return []
        plugins: list[type[StagePlugin]] = []
        for py_file in sorted(self.plugin_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            module = self._load_module(py_file)
            if module is None:
                continue
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, StagePlugin)
                    and attr is not StagePlugin
                ):
                    plugins.append(attr)
        return plugins

    def load_hooks(self) -> list[type[BaseHook]]:
        if not self.plugin_dir.exists():
            return []
        hooks: list[type[BaseHook]] = []
        for py_file in sorted(self.plugin_dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            module = self._load_module(py_file)
            if module is None:
                continue
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseHook)
                    and attr is not BaseHook
                ):
                    hooks.append(attr)
        return hooks

    def _load_module(self, py_file: Path) -> Any:
        try:
            module_name = f"_iperson_external_{py_file.stem}"
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
        except Exception:
            return None


class PipPluginLoader:
    """Load plugins from installed pip packages matching a prefix."""

    def __init__(self, prefix: str = "iperson_plugin_") -> None:
        self.prefix = prefix

    def load_plugins(self) -> list[type[StagePlugin]]:
        plugins: list[type[StagePlugin]] = []
        for module_name in self._find_installed_packages():
            try:
                module = importlib.import_module(module_name)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, StagePlugin)
                        and attr is not StagePlugin
                    ):
                        plugins.append(attr)
            except Exception:
                continue
        return plugins

    def load_hooks(self) -> list[type[BaseHook]]:
        hooks: list[type[BaseHook]] = []
        for module_name in self._find_installed_packages():
            try:
                module = importlib.import_module(module_name)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseHook)
                        and attr is not BaseHook
                    ):
                        hooks.append(attr)
            except Exception:
                continue
        return hooks

    def _find_installed_packages(self) -> list[str]:
        try:
            import pkg_resources

            return [
                pkg.key
                for pkg in pkg_resources.working_set
                if pkg.key.startswith(self.prefix)
            ]
        except Exception:
            return []
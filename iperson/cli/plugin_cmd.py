from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from iperson.pipeline.hook import HookRegistry
from iperson.pipeline.loader import FilePluginLoader, PipPluginLoader
from iperson.pipeline.agent_registry import AgentRegistry

plugin_group = typer.Typer(help="Plugin management")
console = Console()


@plugin_group.command()
def list_plugins() -> None:
    """List all installed plugins and agent nodes."""
    agent_registry = AgentRegistry()
    agent_registry.register("research", description="Research agent", category="research")
    agent_registry.register("generate", description="Content generation agent", category="generation")
    agent_registry.register("publish", description="Multi-platform publish agent", category="publish")

    hook_registry = HookRegistry()
    from iperson.pipeline.hooks import register_builtin_hooks

    register_builtin_hooks(hook_registry)

    # Load external plugins
    ext_dir = Path("~/.iperson/plugins").expanduser()
    file_loader = FilePluginLoader(ext_dir)
    for cls in file_loader.load_plugins():
        plugin_registry.register(cls)
    for cls in file_loader.load_hooks():
        hook_registry.register(cls)

    pip_loader = PipPluginLoader()
    for cls in pip_loader.load_plugins():
        plugin_registry.register(cls)
    for cls in pip_loader.load_hooks():
        hook_registry.register(cls)

    # Display agent nodes
    nodes = agent_registry.list_nodes()
    if nodes:
        table = Table(title="Available Agent Nodes")
        table.add_column("ID", style="cyan")
        table.add_column("Description")
        table.add_column("Category", style="magenta")
        for n in nodes:
            table.add_row(n["node_id"], n["description"], n["category"])
        console.print(table)

    # Display hooks
    hooks = hook_registry.list_hooks()
    if hooks:
        table = Table(title="Installed Hooks")
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Hook Point", style="magenta")
        table.add_column("Version", style="dim")
        for h in hooks:
            table.add_row(
                h["hook_id"], h["name"], h["hook_point"], h["version"]
            )
        console.print(table)

    if not plugins and not hooks:
        console.print("[yellow]No plugins or hooks installed.[/yellow]")


@plugin_group.command()
def install(
    package: str = typer.Argument(..., help="Pip package name"),
) -> None:
    """Install a plugin from pip."""
    import subprocess

    result = subprocess.run(
        ["uv", "pip", "install", package],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        console.print(f"[green]Installed: {package}[/green]")
    else:
        console.print(f"[red]Error:[/red] {result.stderr.strip()}")
        raise typer.Exit(1)


@plugin_group.command()
def remove(
    package: str = typer.Argument(..., help="Pip package name"),
) -> None:
    """Remove a plugin installed via pip."""
    import subprocess

    result = subprocess.run(
        ["uv", "pip", "uninstall", package, "-y"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        console.print(f"[green]Removed: {package}[/green]")
    else:
        console.print(f"[red]Error:[/red] {result.stderr.strip()}")
        raise typer.Exit(1)
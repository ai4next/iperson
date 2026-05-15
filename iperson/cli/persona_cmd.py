from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from iperson.core.persona.profile import (
    PERSONAS_DIR,
    create_default_persona,
    list_personas,
    save_persona,
)

persona_group = typer.Typer(help="Persona management")

console = Console()


@persona_group.command()
def create(
    name: str = typer.Argument(..., help="Persona name"),
) -> None:
    """Create a new persona with a soul.md file."""
    persona_dir = PERSONAS_DIR / name
    soul_path = persona_dir / "soul.md"
    if soul_path.exists():
        console.print(f"[yellow]Warning:[/yellow] Persona '{name}' already exists at {soul_path}")
        overwrite = typer.confirm("Overwrite?")
        if not overwrite:
            console.print("[dim]Aborted.[/dim]")
            raise typer.Exit(0)

    persona = create_default_persona(name)
    path = save_persona(persona)
    console.print(f"[green]Created persona '{name}' at {path}[/green]")
    console.print()
    console.print("[dim]Edit the soul.md to define your persona's voice:[/dim]")
    console.print(f"  vim {path}")


@persona_group.command(name="list")
def list_personas_cmd() -> None:
    """List all available personas."""
    names = list_personas()
    if not names:
        console.print("[yellow]No personas found. Create one with: iperson persona create <name>[/yellow]")
        return

    table = Table(title="Available Personas")
    table.add_column("Name", style="cyan")
    table.add_column("Path", style="dim")

    for name in names:
        soul_path = PERSONAS_DIR / name / "soul.md"
        table.add_row(name, str(soul_path))

    console.print(table)
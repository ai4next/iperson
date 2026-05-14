from __future__ import annotations

from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

from iperson.core.persona.profile import create_default_persona, save_persona_to_file

persona_group = typer.Typer(help="Persona management")

console = Console()


@persona_group.command()
def create(
    name: str = typer.Argument(..., help="Persona name"),
) -> None:
    """Create a new persona profile."""
    personas_dir = Path("~/.iperson/personas").expanduser()
    personas_dir.mkdir(parents=True, exist_ok=True)

    target_path = personas_dir / f"{name}.yaml"
    if target_path.exists():
        console.print(f"[yellow]Warning:[/yellow] Persona '{name}' already exists at {target_path}")
        overwrite = typer.confirm("Overwrite?")
        if not overwrite:
            console.print("[dim]Aborted.[/dim]")
            raise typer.Exit(0)

    persona = create_default_persona(name)
    save_persona_to_file(persona, str(target_path))
    console.print(f"[green]Created persona '{name}' at {target_path}[/green]")


@persona_group.command(name="list")
def list_personas() -> None:
    """List all available personas."""
    personas_dir = Path("~/.iperson/personas").expanduser()

    if not personas_dir.exists():
        console.print("[yellow]No personas found. Create one with: iperson persona create <name>[/yellow]")
        return

    yaml_files = sorted(personas_dir.glob("*.yaml"))
    if not yaml_files:
        console.print("[yellow]No personas found. Create one with: iperson persona create <name>[/yellow]")
        return

    table = Table(title="Available Personas")
    table.add_column("Name", style="cyan")
    table.add_column("Keywords", style="magenta")
    table.add_column("Tone", style="white")

    for yf in yaml_files:
        try:
            data = yaml.safe_load(yf.read_text(encoding="utf-8")) or {}
            pname = data.get("name", yf.stem)
            keywords = ", ".join(data.get("keywords", [])) or "-"
            tone = data.get("tone_instruction", "") or "-"
            # Truncate long tone values
            if len(tone) > 60:
                tone = tone[:57] + "..."
            table.add_row(pname, keywords, tone)
        except Exception:
            table.add_row(yf.stem, "[red]parse error[/red]", "[red]parse error[/red]")

    console.print(table)
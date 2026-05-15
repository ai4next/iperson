from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from iperson.tuning.engine import StyleTuningEngine

tuning_group = typer.Typer(help="Style tuning and persona optimization")
console = Console()


@tuning_group.command()
def analyze(
    persona: str = typer.Option("default", "--persona", "-p", help="Persona name"),
) -> None:
    """Analyze persona style and suggest improvements."""
    engine = StyleTuningEngine()

    all_suggestions = engine.suggest_style_adjustments(persona)
    if not all_suggestions:
        console.print("[yellow]No tuning suggestions available. Generate more content first.[/yellow]")
        raise typer.Exit()

    table = Table(title=f"风格调优建议 — {persona}")
    table.add_column("Dimension", style="cyan")
    table.add_column("Current", style="yellow")
    table.add_column("Suggestion", style="green")
    table.add_column("Reason")
    table.add_column("Confidence", justify="right")

    for s in all_suggestions:
        table.add_row(
            s.dimension,
            s.current_value,
            s.suggested_value,
            s.reason,
            f"{s.confidence:.2f}",
        )

    console.print(table)
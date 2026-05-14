from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from iperson.topics.engine import TopicSuggestionEngine

topics_group = typer.Typer(help="Topic suggestions and auto-selection")
console = Console()


@topics_group.command()
def suggest(
    count: int = typer.Option(5, "--count", "-n", help="Number of suggestions"),
) -> None:
    """Suggest topics for content creation."""
    engine = TopicSuggestionEngine()
    suggestions = engine.suggest_all(top_n=count)

    if not suggestions:
        console.print("[yellow]No topic suggestions available. Import KB docs first with `iperson kb import`[/yellow]")
        raise typer.Exit()

    table = Table(title="选题建议")
    table.add_column("Topic", style="cyan")
    table.add_column("Source", style="magenta")
    table.add_column("Score", justify="right")
    table.add_column("Reason")

    for s in suggestions:
        table.add_row(s.topic[:50], s.source, f"{s.score:.2f}", s.reason)

    console.print(table)
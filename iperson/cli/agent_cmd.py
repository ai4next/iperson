from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from iperson.agent.engine import DigitalTwinAgent

agent_group = typer.Typer(help="Autonomous content agent operations")
console = Console()


@agent_group.command()
def run(
    topic: str = typer.Argument(..., help="Content topic"),
    persona: str = typer.Option("default", "--persona", "-p", help="Persona name"),
) -> None:
    """Run a single autonomous content cycle."""
    agent = DigitalTwinAgent({"persona": persona})
    run_result = asyncio.run(agent.run_once(topic))

    if run_result.status == "failed":
        console.print(f"[red]✗[/red] Agent run failed: {run_result.error}")
    else:
        console.print(f"[green]✓[/green] Agent run completed: [bold]{run_result.topic}[/bold]")
        console.print(f"  Status: {run_result.status}")
        console.print(f"  Content ID: {run_result.content_id}")


@agent_group.command()
def auto(
    count: int = typer.Option(1, "--count", "-n", help="Number of articles to generate"),
) -> None:
    """Automatically select topics and generate content."""
    agent = DigitalTwinAgent()
    runs = asyncio.run(agent.run_autonomous(count=count))

    if not runs:
        console.print("[yellow]No topics available. Import KB docs first.[/yellow]")
        raise typer.Exit()

    table = Table(title="Autonomous Content Generation Results")
    table.add_column("Topic", style="cyan")
    table.add_column("Status")
    table.add_column("Content ID", style="dim")

    for r in runs:
        status_style = "green" if r.status == "completed" else "red"
        table.add_row(r.topic, f"[{status_style}]{r.status}[/{status_style}]", r.content_id[:16])

    console.print(table)
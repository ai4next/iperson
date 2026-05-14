from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

audit_group = typer.Typer(help="Audit content")

console = Console()


@audit_group.command()
def report(
    output_dir: str = typer.Argument(..., help="Output directory path"),
) -> None:
    """Show audit report for generated content."""
    report_path = Path(output_dir).expanduser() / "audit_report.json"

    if not report_path.exists():
        console.print(f"[red]Error:[/red] Audit report not found at {report_path}")
        raise typer.Exit(1)

    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        console.print(f"[red]Error:[/red] Invalid JSON: {e}")
        raise typer.Exit(1) from e

    # Overall status
    status = data.get("overall_status", "unknown")
    status_style = {
        "pass": "green",
        "review": "yellow",
        "fail": "red",
    }.get(status, "white")

    console.print(f"[bold]Audit Report[/bold] — Status: [{status_style}]{status}[/{status_style}]")
    console.print(f"Report ID: {data.get('id', '?')}")
    console.print(f"Content ID: {data.get('content_id', '?')}")
    console.print(f"Created: {data.get('created_at', '?')}")

    # Dimension scores
    scores = data.get("scores", {})
    if scores:
        table = Table(title="Dimension Scores")
        table.add_column("Dimension", style="cyan")
        table.add_column("Score", style="magenta")

        for dim, score in sorted(scores.items()):
            score_style = "green" if score >= 0.7 else ("yellow" if score >= 0.4 else "red")
            table.add_row(dim, f"[{score_style}]{score:.2f}[/{score_style}]")

        console.print()
        console.print(table)

    # Dimension details
    dimensions = data.get("dimensions", {})
    if dimensions:
        console.print()
        console.print("[bold]Dimension Details:[/bold]")
        for dim_name, dim_data in sorted(dimensions.items()):
            score = dim_data.get("score", 0.0)
            details = dim_data.get("details", dim_data.get("message", ""))
            score_style = "green" if score >= 0.7 else ("yellow" if score >= 0.4 else "red")
            console.print(f"  [{score_style}]{dim_name}: {score:.2f}[/{score_style}]")
            if details:
                console.print(f"    {details}")
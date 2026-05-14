from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from iperson.analytics.engine import AnalyticsEngine

analytics_group = typer.Typer(help="Content analytics and performance tracking")
console = Console()


@analytics_group.command()
def collect(
    content_id: str = typer.Argument(..., help="Content ID"),
    platform: str = typer.Option("xiaohongshu", "--platform", help="Platform name"),
    views: int = typer.Option(0, "--views", help="View count"),
    likes: int = typer.Option(0, "--likes", help="Like count"),
    shares: int = typer.Option(0, "--shares", help="Share count"),
    comments: int = typer.Option(0, "--comments", help="Comment count"),
) -> None:
    """Record content performance metrics."""
    engine = AnalyticsEngine()
    metrics = engine.collect_metrics(
        content_id, platform, views, likes, shares, comments
    )
    console.print(
        f"[green]✓[/green] Metrics recorded for content [bold]{content_id}[/bold] on {platform}"
    )


@analytics_group.command()
def report(content_id: str = typer.Argument(..., help="Content ID")) -> None:
    """Show performance report for content."""
    engine = AnalyticsEngine()
    summary = engine.get_summary(content_id)
    metrics_list = engine.get_metrics(content_id)

    if not metrics_list:
        console.print("[yellow]No metrics found for this content.[/yellow]")
        raise typer.Exit()

    table = Table(title=f"Content Report: {content_id[:16]}...")
    table.add_column("Platform", style="cyan")
    table.add_column("Views", justify="right")
    table.add_column("Likes", justify="right")
    table.add_column("Shares", justify="right")
    table.add_column("Comments", justify="right")
    table.add_column("Collected At", style="dim")

    for m in metrics_list:
        table.add_row(
            m["platform"],
            str(m["views"]),
            str(m["likes"]),
            str(m["shares"]),
            str(m["comments"]),
            m["collected_at"][:19],
        )

    console.print(table)

    from iperson.analytics.report import format_summary

    console.print(format_summary(summary))
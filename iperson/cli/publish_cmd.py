from __future__ import annotations

import asyncio
from pathlib import Path

import numpy as np
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from iperson.config import ensure_data_dirs
from iperson.core.kb.embedder import OpenAIEmbedder
from iperson.core.kb.vector_store import VectorStore
from iperson.core.persona.engine import PersonaEngine
from iperson.core.persona.profile import (
    PERSONAS_DIR,
    create_default_persona,
    load_persona,
)
from iperson.pipeline.context import PipelineContext
from iperson.pipeline.orchestrator import PipelineOrchestrator
from iperson.pipeline.plugins import register_builtin_plugins
from iperson.pipeline.pipeline import load_pipeline
from iperson.pipeline.registry import PluginRegistry
from iperson.storage import init_db
from iperson.storage.db import get_connection
from iperson.utils.llm import get_llm
from iperson.utils.output import (
    create_output_dir,
    write_article,
    write_audit_report,
    write_platform_content,
)

publish_group = typer.Typer(help="Run content pipeline and publish")

console = Console()


@publish_group.command()
def run(
    topic: str = typer.Argument(..., help="Content topic"),
    recipe: str = typer.Option("quick", "--recipe", "-r", help="Pipeline recipe name"),
    persona: str = typer.Option("", "--persona", "-p", help="Persona name"),
    platform: str = typer.Option("xiaohongshu", "--platform", help="Target platform"),
    verbose: bool = typer.Option(False, "--verbose", help="Show detailed output"),
) -> None:
    """Run the content generation pipeline and publish."""
    asyncio.run(_run_pipeline(topic, recipe, persona, platform, verbose))


async def _run_pipeline(
    topic: str,
    recipe_name: str,
    persona_name: str,
    platform: str,
    verbose: bool,
) -> None:
    """Execute the full content pipeline."""
    # Initialize infrastructure
    ensure_data_dirs()
    init_db()

    # LLM client
    llm_client = get_llm("generation")

    # Load recipe
    try:
        recipe_data = load_pipeline(recipe_name)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
    if verbose:
        console.print(f"[dim]Loaded recipe:[/dim] {recipe_data.get('name', recipe_name)}")

    # Load or create persona
    persona_profile = load_persona(persona_name or "default")
    if persona_profile is None:
        if persona_name:
            msg = (
                f"[yellow]Warning:[/yellow] Persona '{persona_name}' "
                f"not found at {PERSONAS_DIR / persona_name / 'soul.md'}, using defaults"
            )
            console.print(msg)
        persona_profile = create_default_persona(persona_name or "default")

    persona_engine = PersonaEngine(persona_profile)

    # Plugin registry
    registry = PluginRegistry()
    register_builtin_plugins(registry)
    if verbose:
        registered = registry.list_plugins()
        console.print(f"[dim]Registered {len(registered)} built-in plugins[/dim]")

    # Pipeline context
    ctx = PipelineContext(
        persona_name=persona_profile.name,
        topic=topic,
        recipe_name=recipe_name,
    )
    ctx.data["llm_client"] = llm_client
    ctx.data["persona_engine"] = persona_engine
    ctx.data["platform"] = platform

    # Load KB context via vector search
    try:
        ctx = await _load_kb_context(ctx, topic)
    except Exception as e:
        console.print(f"[yellow]Warning:[/yellow] KB retrieval failed ({e}), continuing without KB grounding.")

    # Run pipeline
    orchestrator = PipelineOrchestrator(registry)
    if verbose:
        console.print("[bold]Running pipeline...[/bold]")

    result = await orchestrator.run(ctx, recipe_data)

    # Output directory
    out_dir = create_output_dir(topic)

    # Write outputs
    if result.generated_content:
        write_article(out_dir, result.generated_content)

    if result.humanized_content:
        humanized_path = out_dir / "humanized_article.md"
        humanized_path.write_text(result.humanized_content, encoding="utf-8")

    if result.audit_result:
        write_audit_report(out_dir, result.audit_result)

    if result.platform_contents:
        for plat, content in result.platform_contents.items():
            write_platform_content(out_dir, plat, content)

    # Display results
    _show_results(result, out_dir, verbose)


async def _load_kb_context(ctx: PipelineContext, topic: str) -> PipelineContext:
    """Load relevant KB chunks via vector search and set on pipeline context."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT c.id, c.content, c.chunk_index, c.embedding, d.title as doc_title
               FROM kb_chunks c
               JOIN kb_docs d ON c.kb_doc_id = d.id
               WHERE c.embedding IS NOT NULL
               ORDER BY c.created_at DESC"""
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return ctx

    vs = VectorStore()
    for row in rows:
        emb = np.frombuffer(row["embedding"], dtype=np.float64).tolist()
        vs.add(emb, {
            "text": row["content"],
            "metadata": {},
            "doc_title": row["doc_title"],
        })

    embedder = OpenAIEmbedder()
    query_vector = await embedder.embed(topic)
    results = vs.search(query_vector, top_k=5)

    ctx.kb_chunks = results
    return ctx


def _show_results(ctx: PipelineContext, out_dir: Path, verbose: bool) -> None:
    """Display pipeline results using Rich components."""
    # Summary panel
    status_style = "green" if ctx.status == "completed" else "yellow"
    summary_lines = [
        f"Status: [{status_style}]{ctx.status}[/{status_style}]",
        f"Topic: {ctx.topic}",
        f"Output: [blue]{out_dir}[/blue]",
    ]
    if ctx.errors:
        summary_lines.append(f"Errors: [red]{len(ctx.errors)}[/red]")

    console.print()
    console.print(Panel(
        "\n".join(summary_lines),
        title="[bold]Pipeline Complete[/bold]",
        border_style="green" if not ctx.errors else "yellow",
    ))

    # Stage timing table
    timing_keys = [k for k in ctx.data if k.startswith("_timing_")]
    if timing_keys:
        table = Table(title="Stage Timings", border_style="dim")
        table.add_column("Stage", style="cyan")
        table.add_column("Duration", style="magenta", justify="right")
        for key in sorted(timing_keys):
            stage_name = key.replace("_timing_", "")
            duration = ctx.data[key]
            table.add_row(stage_name, f"{duration:.2f}s")
        console.print(table)

    # Generated content preview
    if ctx.generated_content:
        word_count = len(ctx.generated_content)
        preview = ctx.generated_content[:300]
        if len(ctx.generated_content) > 300:
            preview += "..."
        info = Text(f"Word count: {word_count}  |  Preview:", style="dim")
        console.print(Panel(
            preview,
            title="[bold]Generated Content[/bold]",
            subtitle=info,
            border_style="blue",
        ))

    # Humanized content diff
    if ctx.humanized_content and ctx.humanized_content != ctx.generated_content:
        original_len = len(ctx.generated_content or "")
        humanized_len = len(ctx.humanized_content)
        diff = humanized_len - original_len
        info = Text(
            f"Original: {original_len} chars → Humanized: {humanized_len} chars ({diff:+d})",
            style="dim",
        )
        preview = ctx.humanized_content[:200]
        if len(ctx.humanized_content) > 200:
            preview += "..."
        console.print(Panel(
            preview,
            title="[bold]Humanized Content[/bold]",
            subtitle=info,
            border_style="green",
        ))

    # Audit result
    if ctx.audit_result:
        scores = ctx.audit_result.get("scores", {})
        status = ctx.audit_result.get("overall_status", "unknown")
        status_icon = {"pass": "✓", "review": "△", "fail": "✗"}.get(status, "?")
        status_color = {"pass": "green", "review": "yellow", "fail": "red"}.get(status, "white")

        audit_table = Table(
            title=f"Audit Report — [{status_color}]{status_icon} {status}[/{status_color}]",
            border_style="dim",
        )
        audit_table.add_column("Dimension", style="cyan")
        audit_table.add_column("Score", justify="right")
        audit_table.add_column("Status", justify="center")

        # Chinese dimension labels for better readability
        dim_labels = {
            "grounding": "事实依据",
            "keyword_fit": "关键词合规",
            "structure": "结构质量",
            "platform_rules": "平台规则",
            "style_consistency": "风格一致",
            "ai_score": "AI 浓度",
        }

        for dim, score in sorted(scores.items()):
            label = dim_labels.get(dim, dim)
            if dim == "ai_score":
                # AI score: lower is better, invert for display
                display_score = 1.0 - score
                score_style = (
                    "green" if display_score >= 0.7
                    else "yellow" if display_score >= 0.4
                    else "red"
                )
                status_text = "pass" if score <= 0.35 else "review"
            else:
                score_style = "green" if score >= 0.7 else ("yellow" if score >= 0.4 else "red")
                display_score = score
                status_text = "pass" if score >= 0.7 else ("review" if score >= 0.4 else "fail")

            audit_table.add_row(
                label,
                f"[{score_style}]{display_score:.2f}[/{score_style}]",
                f"[{score_style}]{status_text}[/{score_style}]",
            )
        console.print(audit_table)

    # Publish results
    if ctx.publish_results:
        pub_table = Table(title="Publish Results", border_style="dim")
        pub_table.add_column("Platform", style="cyan")
        pub_table.add_column("Status", justify="center")
        pub_table.add_column("Output", style="dim")
        for pub in ctx.publish_results:
            platform = pub.get("platform", "?")
            pub_status = pub.get("status", "ok")
            status_icon = {"ok": "✓", "skipped": "→", "failed": "✗"}.get(pub_status, "?")
            status_colors = {"ok": "green", "skipped": "yellow", "failed": "red"}
            status_color = status_colors.get(pub_status, "white")
            output_path = pub.get("output_path", "")
            pub_table.add_row(
                platform,
                f"[{status_color}]{status_icon} {pub_status}[/{status_color}]",
                str(output_path) if output_path else "",
            )
        console.print(pub_table)

    # Output files
    if out_dir.exists():
        files = sorted(out_dir.rglob("*"))
        text_files = [f for f in files if f.is_file() and f.suffix in (".md", ".json")]
        if text_files:
            file_list = "\n".join(
                f"  [blue]{f.relative_to(out_dir.parent)}[/blue]"
                for f in text_files
            )
            console.print(Panel(
                file_list,
                title="[bold]Output Files[/bold]",
                border_style="dim",
            ))

    # Errors
    if ctx.errors:
        console.print()
        console.print("[bold red]Errors:[/bold red]")
        for err in ctx.errors:
            console.print(f"  - [red]{err.get('stage', '?')}:[/red] {err.get('error', '?')}")


@publish_group.command()
def status(
    publication_id: str = typer.Argument(None, help="Publication ID (optional)"),
) -> None:
    """View publication queue status."""
    from iperson.publish.engine import PublishEngine

    engine = PublishEngine()
    if publication_id:
        pubs = [p for p in engine.list_publications() if p["id"] == publication_id]
    else:
        pubs = engine.list_publications()

    if not pubs:
        console.print("[yellow]No publications found.[/yellow]")
        raise typer.Exit()

    table = Table(title="Publication Queue")
    table.add_column("ID", style="dim")
    table.add_column("Content ID", style="cyan")
    table.add_column("Platform", style="magenta")
    table.add_column("Status")
    table.add_column("Scheduled At", style="dim")
    table.add_column("Error", style="red")

    for p in pubs[:20]:
        status_style = {
            "draft": "dim",
            "queued": "yellow",
            "publishing": "blue",
            "published": "green",
            "failed": "red",
        }.get(p["status"], "white")
        table.add_row(
            p["id"][:12],
            p["content_id"][:12],
            p["platform"],
            f"[{status_style}]{p['status']}[/{status_style}]",
            p.get("scheduled_at", "")[:19] if p.get("scheduled_at") else "-",
            p.get("error_message", "")[:30] if p.get("error_message") else "-",
        )
    console.print(table)


@publish_group.command()
def schedule(
    publication_id: str = typer.Argument(..., help="Publication ID"),
    at: str = typer.Option(
        ...,
        "--at",
        help="Scheduled time (ISO format, e.g. 2026-05-16T10:00:00)",
    ),
) -> None:
    """Schedule a publication for later."""
    from iperson.publish.engine import PublishEngine
    from iperson.storage.db import get_connection

    engine = PublishEngine()
    try:
        engine.update_status(publication_id, "queued")
        conn = get_connection()
        try:
            conn.execute(
                "UPDATE publications SET scheduled_at = ? WHERE id = ?",
                (at, publication_id),
            )
            conn.commit()
        finally:
            conn.close()
        console.print(
            f"[green]Publication {publication_id[:12]} scheduled at {at}[/green]"
        )
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@publish_group.command()
def retry(
    publication_id: str = typer.Argument(..., help="Publication ID"),
) -> None:
    """Retry a failed publication."""
    from iperson.publish.engine import PublishEngine

    engine = PublishEngine()
    try:
        engine.update_status(publication_id, "publishing", error="")
        console.print(
            f"[green]Retrying publication {publication_id[:12]}[/green]"
        )
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

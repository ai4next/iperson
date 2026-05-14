from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from iperson.config import ensure_data_dirs
from iperson.core.persona.engine import PersonaEngine
from iperson.core.persona.profile import (
    create_default_persona,
    load_persona_from_file,
)
from iperson.pipeline.context import PipelineContext
from iperson.pipeline.orchestrator import PipelineOrchestrator
from iperson.pipeline.plugins import register_builtin_plugins
from iperson.pipeline.recipe import load_recipe
from iperson.pipeline.registry import PluginRegistry
from iperson.storage import init_db
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
        recipe_data = load_recipe(recipe_name)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1) from e
    if verbose:
        console.print(f"[dim]Loaded recipe:[/dim] {recipe_data.get('name', recipe_name)}")

    # Load or create persona
    persona_path = Path(f"~/.iperson/personas/{persona_name or 'default'}.yaml").expanduser()
    if persona_path.exists():
        persona_profile = load_persona_from_file(persona_path)
        if verbose:
            console.print(f"[dim]Loaded persona:[/dim] {persona_profile.name}")
    else:
        if persona_name:
            msg = (
                f"[yellow]Warning:[/yellow] Persona '{persona_name}' "
                f"not found at {persona_path}, using defaults"
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
        persona_id=persona_profile.name,
        topic=topic,
        recipe_name=recipe_name,
    )
    ctx.data["llm_client"] = llm_client
    ctx.data["persona_engine"] = persona_engine
    ctx.data["platform"] = platform

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

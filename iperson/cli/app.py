from __future__ import annotations

import typer

from iperson.cli.analytics_cmd import analytics_group
from iperson.cli.audit_cmd import audit_group
from iperson.cli.kb_cmd import kb_group
from iperson.cli.persona_cmd import persona_group
from iperson.cli.publish_cmd import publish_group
from iperson.cli.topics_cmd import topics_group
from iperson.cli.tuning_cmd import tuning_group

app = typer.Typer(
    name="iperson",
    help="iPerson — KB-first personal IP content engine",
    no_args_is_help=True,
)

app.add_typer(analytics_group, name="analytics")
app.add_typer(publish_group, name="publish")
app.add_typer(kb_group, name="kb")
app.add_typer(audit_group, name="audit")
app.add_typer(persona_group, name="persona")
app.add_typer(topics_group, name="topics")
app.add_typer(tuning_group, name="tuning")


@app.callback(invoke_without_command=True)
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version",
        is_eager=True,
    ),
    ctx: typer.Context = typer.Context,
) -> None:
    """iPerson CLI — Manage your personal IP operations."""
    if version:
        from iperson import __version__

        typer.echo(f"iPerson v{__version__}")
        raise typer.Exit()
    # If no command was invoked, show help
    if ctx.invoked_subcommand is None:
        typer.echo(app.get_help_text())
        raise typer.Exit()


def main() -> None:
    """Entry point for the CLI application."""
    app()


if __name__ == "__main__":
    main()
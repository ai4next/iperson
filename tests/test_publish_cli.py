from __future__ import annotations

from typer.testing import CliRunner
from iperson.cli.app import app

runner = CliRunner()


class TestPublishCli:
    def test_publish_status_help(self) -> None:
        result = runner.invoke(app, ["publish", "status", "--help"])
        assert result.exit_code == 0
        assert "publication" in result.stdout.lower()

    def test_publish_schedule_help(self) -> None:
        result = runner.invoke(app, ["publish", "schedule", "--help"])
        assert result.exit_code == 0
        assert "schedule" in result.stdout.lower()
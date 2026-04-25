from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from agentctl import __version__
from agentctl.cli.apply import run_apply
from agentctl.cli.deploy import run_deploy
from agentctl.cli.doctor import run_doctor

app = typer.Typer(
    name="agentctl",
    help="Manage agent manifests like kubectl manages cluster resources.",
    no_args_is_help=True,
)
console = Console()


@app.callback()
def _main(
    version: bool = typer.Option(False, "--version", help="Show version and exit."),
) -> None:
    if version:
        console.print(__version__)
        raise typer.Exit(0)


@app.command("apply")
def apply(
    manifest: Path = typer.Argument(..., exists=True, readable=True, help="Path to agent YAML manifest."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print actions without writing files."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing generated files under .agents/."),
) -> None:
    """Validate manifest and write codegen output to .agents/{name}/."""
    run_apply(manifest, dry_run=dry_run, force=force)


@app.command("deploy")
def deploy(
    agent_name: str = typer.Argument(..., help="Agent name (directory under .agents/)."),
    apply_first: bool = typer.Option(
        False,
        "--apply",
        help="Run apply first using examples/agents/{name}.yaml if present.",
    ),
    manifest: Path | None = typer.Option(
        None,
        "--manifest",
        "-f",
        help="Manifest path when using --apply.",
    ),
    no_compose: bool = typer.Option(False, "--no-compose", help="Only build the image; do not run compose up."),
) -> None:
    """Build Docker image for an agent and run it via docker compose."""
    run_deploy(agent_name, apply_first=apply_first, manifest=manifest, no_compose=no_compose)


@app.command("doctor")
def doctor() -> None:
    """Check docker and related tools."""
    run_doctor()


def main() -> None:
    app()


if __name__ == "__main__":
    main()

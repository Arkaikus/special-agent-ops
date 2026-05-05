from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from agentctl import __version__
from agentctl.cli.apply import run_apply
from agentctl.cli.chat import run_chat
from agentctl.cli.deploy import run_deploy
from agentctl.cli.doctor import run_doctor
from agentctl.cli.exec_ import run_exec
from agentctl.cli.list_agents import run_list
from agentctl.cli.logs import run_logs
from agentctl.cli.project import project_app
from agentctl.cli.undeploy import run_undeploy

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
    manifest: Path = typer.Argument(
        ...,
        help="Path to agent manifest (.yaml or .md with frontmatter).",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print actions without writing files."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing generated files under .cache/."),
) -> None:
    """Validate manifest and write codegen output to .cache/{name}/."""
    if not manifest.exists():
        console.print(f"[red]Manifest not found: {manifest}[/red]")
        raise typer.Exit(1)
    if not manifest.is_file():
        console.print(f"[red]Manifest path is not a file: {manifest}[/red]")
        raise typer.Exit(1)
    run_apply(manifest, dry_run=dry_run, force=force)


@app.command("deploy")
def deploy(
    agent_name: str = typer.Argument(..., help="Agent name (directory under .cache/)."),
    apply_first: bool = typer.Option(
        False,
        "--apply",
        help="Run apply first using .agents/{name}.md or examples/agents/{name}.yaml if present.",
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


@app.command("undeploy")
def undeploy(
    agent_name: str = typer.Argument(..., help="Agent name (directory under .cache/)."),
    volumes: bool = typer.Option(False, "--volumes", "-v", help="Also remove named volumes."),
    images: bool = typer.Option(False, "--images", "-i", help="Also remove locally built images."),
) -> None:
    """Bring down a deployed agent service (docker compose down)."""
    run_undeploy(agent_name, remove_volumes=volumes, remove_images=images)


@app.command("list")
def list_agents(
    agents_dir: Path | None = typer.Option(
        None,
        "--dir",
        "-d",
        help="Override the .cache/ directory to inspect.",
    ),
) -> None:
    """List all agents scaffolded under .cache/ with their runtime and compose config."""
    run_list(agents_dir)


@app.command("exec")
def exec_agent(
    agent_name: str = typer.Argument(..., help="Agent name (directory under .cache/)."),
    shell: str = typer.Option("/bin/bash", "--shell", "-s", help="Shell to launch inside the container."),
) -> None:
    """Attach an interactive shell inside a running agent container."""
    run_exec(agent_name, shell=shell)


@app.command("logs")
def logs(
    agent_name: str = typer.Argument(..., help="Agent name (directory under .cache/)."),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output."),
    tail: int | None = typer.Option(None, "--tail", "-n", help="Number of lines to show from the end."),
    since: str | None = typer.Option(None, "--since", help="Show logs since timestamp or duration (e.g. 5m, 1h)."),
) -> None:
    """Show docker compose logs for a deployed agent (useful for debugging output)."""
    run_logs(agent_name, follow=follow, tail=tail, since=since)


@app.command("doctor")
def doctor() -> None:
    """Check docker and related tools."""
    run_doctor()


@app.command("chat")
def chat(
    agent: str = typer.Argument(..., help="Agent name to chat with (supports @agent syntax)."),
    message: str | None = typer.Argument(None, help="Message to send. Omit for interactive mode."),
    gateway: str = typer.Option(
        "http://localhost:8000",
        "--gateway",
        "-g",
        envvar="AGENTCTL_GATEWAY_URL",
        help="Agent gateway base URL.",
    ),
    workspace: Path = typer.Option(
        Path(".workspace"),
        "--workspace",
        "-w",
        help="Workspace folder for @file references.",
    ),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Stream the agent response."),
) -> None:
    """Chat directly with a deployed agent via the gateway.

    Agent name may be prefixed with @ (e.g. @architect).
    Messages may reference workspace files with @filename (e.g. @docs/adr.md).
    Omit MESSAGE to enter interactive mode.
    """
    run_chat(
        agent=agent,
        message=message,
        gateway_url=gateway,
        workspace=workspace,
        stream=stream,
    )


app.add_typer(project_app, name="project")


def main() -> None:
    app()


if __name__ == "__main__":
    main()

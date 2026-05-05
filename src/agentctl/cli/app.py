from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from agentctl import __version__
from agentctl.cli.chat import run_chat
from agentctl.cli.doctor import run_doctor
from agentctl.cli.down import run_down
from agentctl.cli.exec_ import run_exec
from agentctl.cli.list_agents import run_list
from agentctl.cli.logs import run_logs
from agentctl.cli.project import project_app
from agentctl.cli.stop import run_stop
from agentctl.cli.up import run_up

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


@app.command("up")
def up(
    agent_name: str | None = typer.Argument(None, help="Agent name to deploy. Omit to deploy all agents."),
    build: bool = typer.Option(False, "--build", help="Regenerate codegen artifacts before building."),
) -> None:
    """Codegen, build and deploy agents from .agents/.

    Processes all agents found in .agents/*.md unless a specific agent name is given.
    Pass --build to force regeneration of codegen artifacts.
    """
    run_up(agent_name, build=build)


@app.command("stop")
def stop(
    agent_name: str | None = typer.Argument(None, help="Agent name to stop. Omit to stop all deployed agents."),
) -> None:
    """Stop running agent containers without removing them."""
    run_stop(agent_name)


@app.command("down")
def down(
    agent_name: str | None = typer.Argument(None, help="Agent name to bring down. Omit to bring down all deployed agents."),
) -> None:
    """Stop and remove agent containers (leaves .cache/ intact)."""
    run_down(agent_name)


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

from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console

console = Console()


def run_undeploy(agent_name: str, *, remove_volumes: bool, remove_images: bool) -> None:
    """Bring down a deployed agent service using docker compose."""
    repo = Path.cwd()
    agent_dir = repo / ".agents" / agent_name

    if not agent_dir.is_dir():
        raise SystemExit(
            f"No agent directory found at {agent_dir}. "
            "Has this agent been applied and deployed?"
        )

    compose_base = repo / "docker-compose.yml"
    compose_agent = agent_dir / "compose.agent.yml"

    if not compose_agent.is_file():
        raise SystemExit(
            f"Missing {compose_agent}. Run `agentctl apply` to regenerate it."
        )

    cmd = [
        "docker",
        "compose",
        "-f",
        str(compose_base),
        "-f",
        str(compose_agent),
        "down",
    ]
    if remove_volumes:
        cmd.append("--volumes")
    if remove_images:
        cmd.append("--rmi")
        cmd.append("local")

    console.print(f"[dim]{' '.join(cmd)}[/dim]")
    subprocess.run(cmd, cwd=repo, check=True)
    console.print(f"[green]Undeployed[/green] agent {agent_name!r}")

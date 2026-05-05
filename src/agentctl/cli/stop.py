from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console

console = Console()


def _resolve_compose_files(repo: Path, agent_name: str | None) -> list[tuple[str, Path, Path]]:
    """Return a list of (name, compose_base, compose_agent) tuples.

    If *agent_name* is given only that agent's compose files are returned.
    Otherwise all cached agents under ``.cache/`` with a ``compose.agent.yml`` are returned.
    """
    cache_dir = repo / ".cache"
    compose_base = repo / "docker-compose.yml"

    if agent_name:
        agent_dir = cache_dir / agent_name
        compose_agent = agent_dir / "compose.agent.yml"
        if not agent_dir.is_dir():
            raise SystemExit(f"No agent directory found at {agent_dir}")
        if not compose_agent.is_file():
            raise SystemExit(f"Missing {compose_agent}; run `agentctl up` first")
        return [(agent_name, compose_base, compose_agent)]

    if not cache_dir.is_dir():
        raise SystemExit(f"No .cache/ directory found at {cache_dir}; run `agentctl up` first")

    entries = []
    for agent_dir in sorted(cache_dir.iterdir()):
        if not agent_dir.is_dir():
            continue
        compose_agent = agent_dir / "compose.agent.yml"
        if compose_agent.is_file():
            entries.append((agent_dir.name, compose_base, compose_agent))

    if not entries:
        raise SystemExit("No deployed agents found under .cache/")
    return entries


def _run(cmd: list[str], cwd: Path) -> None:
    console.print(f"[dim]{' '.join(cmd)}[/dim]")
    subprocess.run(cmd, cwd=cwd, check=True)


def run_stop(agent_name: str | None) -> None:
    """Stop running agent containers without removing them."""
    repo = Path.cwd()
    entries = _resolve_compose_files(repo, agent_name)

    for name, compose_base, compose_agent in entries:
        _run(
            [
                "docker",
                "compose",
                "-f",
                str(compose_base),
                "-f",
                str(compose_agent),
                "stop",
            ],
            cwd=repo,
        )
        console.print(f"[yellow]Stopped[/yellow] agent {name!r}")

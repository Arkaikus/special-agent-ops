from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console

from agentctl.cli.stop import _resolve_compose_files

console = Console()


def _run(cmd: list[str], cwd: Path) -> None:
    console.print(f"[dim]{' '.join(cmd)}[/dim]")
    subprocess.run(cmd, cwd=cwd, check=True)


def run_down(agent_name: str | None) -> None:
    """Stop and remove agent containers (leaves .cache/ intact)."""
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
                "down",
            ],
            cwd=repo,
        )
        console.print(f"[green]Down[/green] agent {name!r} (containers removed; .cache/ preserved)")

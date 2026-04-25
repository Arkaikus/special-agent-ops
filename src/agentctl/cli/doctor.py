from __future__ import annotations

import shutil
import subprocess

from rich.console import Console

console = Console()


def run_doctor() -> None:
    """Verify docker, docker compose, and optional tools are available."""
    for name, check in [
        ("docker", lambda: shutil.which("docker")),
        (
            "docker compose",
            lambda: subprocess.run(["docker", "compose", "version"], capture_output=True).returncode == 0,
        ),
    ]:
        ok = bool(check())
        console.print(f"[green]ok[/green] {name}" if ok else f"[red]missing[/red] {name}")

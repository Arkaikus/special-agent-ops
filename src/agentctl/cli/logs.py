from __future__ import annotations

import subprocess
from pathlib import Path

import yaml
from rich.console import Console

from agentctl.cli.utils import find_repo_root

console = Console()


def run_logs(
    agent_name: str,
    *,
    follow: bool,
    tail: int | None,
    since: str | None,
) -> None:
    """Stream or print docker compose logs for a deployed agent service."""
    repo = find_repo_root()
    agent_dir = (repo / ".cache" / agent_name).resolve()

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

    service = _service_name(compose_agent, agent_name)

    cmd = [
        "docker",
        "compose",
        "-f",
        str(compose_base),
        "-f",
        str(compose_agent),
        "logs",
    ]
    if follow:
        cmd.append("--follow")
    if tail is not None:
        cmd.extend(["--tail", str(tail)])
    if since:
        cmd.extend(["--since", since])
    cmd.append(service)

    console.print(f"[dim]{' '.join(cmd)}[/dim]")
    subprocess.run(cmd, cwd=repo, check=False)


def _service_name(compose_agent: Path, fallback: str) -> str:
    try:
        data = yaml.safe_load(compose_agent.read_text(encoding="utf-8"))
        services = (data or {}).get("services") or {}
        if len(services) == 1:
            return next(iter(services.keys()))
    except Exception:  # noqa: BLE001
        pass
    return fallback

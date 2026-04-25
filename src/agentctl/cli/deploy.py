from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console

from agentctl.cli.apply import run_apply

console = Console()


def run_deploy(
    agent_name: str,
    *,
    apply_first: bool,
    manifest: Path | None,
    no_compose: bool,
) -> None:
    repo = Path.cwd()
    agent_dir = repo / ".agents" / agent_name

    if apply_first:
        mpath = manifest or (repo / "examples" / "agents" / f"{agent_name}.yaml")
        if not mpath.is_file():
            raise SystemExit(f"--apply requires manifest at {mpath} or pass --manifest")
        run_apply(mpath, dry_run=False, force=True)

    if not agent_dir.is_dir():
        raise SystemExit(f"missing {agent_dir}; run `agentctl apply` first")

    image = _image_name(agent_name, agent_dir)
    _run(["docker", "build", "-t", image, str(agent_dir)], cwd=repo)

    if no_compose:
        console.print(f"[green]Built[/green] {image} (skipped compose)")
        return

    compose_base = repo / "docker-compose.yml"
    compose_agent = agent_dir / "compose.agent.yml"
    if not compose_agent.is_file():
        raise SystemExit(f"missing {compose_agent}; run `agentctl apply`")

    service = _service_name(agent_dir, agent_name)
    _run(
        [
            "docker",
            "compose",
            "-f",
            str(compose_base),
            "-f",
            str(compose_agent),
            "up",
            "-d",
            "--build",
            service,
        ],
        cwd=repo,
    )
    console.print(f"[green]Deployed[/green] service {service} image {image}")


def _image_name(agent_name: str, agent_dir: Path) -> str:
    # Parse from compose.agent.yml is heavy; default tag
    return f"agentctl/{agent_name}:local"


def _service_name(agent_dir: Path, fallback: str) -> str:
    import yaml

    p = agent_dir / "compose.agent.yml"
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    services = data.get("services") or {}
    if len(services) == 1:
        return next(iter(services.keys()))
    return fallback


def _run(cmd: list[str], cwd: Path) -> None:
    console.print(f"[dim]{' '.join(cmd)}[/dim]")
    subprocess.run(cmd, cwd=cwd, check=True)

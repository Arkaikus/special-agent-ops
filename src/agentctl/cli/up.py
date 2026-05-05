from __future__ import annotations

import subprocess
from pathlib import Path

from rich.console import Console

from agentctl.cli.apply import run_apply

console = Console()


def _agents_dir(repo: Path) -> Path:
    return repo / ".agents"


def _resolve_agents(repo: Path, agent_name: str | None) -> list[Path]:
    """Return a list of manifest paths from .agents/ to process.

    If *agent_name* is given only that manifest is returned.
    Otherwise all ``*.md`` files under ``.agents/`` are returned.
    """
    agents_dir = _agents_dir(repo)
    if not agents_dir.is_dir():
        raise SystemExit(f"No .agents/ directory found at {agents_dir}")

    if agent_name:
        path = agents_dir / f"{agent_name}.md"
        if not path.is_file():
            raise SystemExit(f"Agent manifest not found: {path}")
        return [path]

    manifests = sorted(agents_dir.glob("*.md"))
    if not manifests:
        raise SystemExit(f"No agent manifests (*.md) found under {agents_dir}")
    return manifests


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


def run_up(agent_name: str | None, *, build: bool) -> None:
    """Codegen, build and deploy agents defined in .agents/."""
    repo = Path.cwd()
    manifests = _resolve_agents(repo, agent_name)

    for manifest_path in manifests:
        name = manifest_path.stem
        agent_dir = repo / ".cache" / name

        needs_codegen = build or not agent_dir.is_dir()
        if needs_codegen:
            console.print(f"[bold]Codegenning[/bold] {name}…")
            run_apply(manifest_path, dry_run=False, force=True)

        if not agent_dir.is_dir():
            raise SystemExit(f"Missing {agent_dir} after codegen — check apply output above")

        image = f"agentctl/{name}:local"
        _run(["docker", "build", "-t", image, str(agent_dir)], cwd=repo)

        compose_base = repo / "docker-compose.yml"
        compose_agent = agent_dir / "compose.agent.yml"
        if not compose_agent.is_file():
            raise SystemExit(f"Missing {compose_agent}; run codegen first")

        service = _service_name(agent_dir, name)
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
                service,
            ],
            cwd=repo,
        )
        console.print(f"[green]Up[/green] service {service!r} ({image})")

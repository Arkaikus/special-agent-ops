from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

import yaml

console = Console()


def run_list(agents_dir: Path | None) -> None:
    """List agents scaffolded under .agents/ and show their basic config."""
    repo = Path.cwd()
    root = agents_dir or (repo / ".agents")

    if not root.is_dir():
        console.print(f"[yellow]No agents directory found at {root}[/yellow]")
        raise SystemExit(0)

    entries = sorted(
        [d for d in root.iterdir() if d.is_dir()],
        key=lambda d: d.name,
    )

    if not entries:
        console.print(f"[yellow]No agents found under {root}[/yellow]")
        raise SystemExit(0)

    table = Table(
        title=f"Agents in {root}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Name", style="bold")
    table.add_column("Runtime")
    table.add_column("Image")
    table.add_column("Port")
    table.add_column("Compose service")
    table.add_column("Has manifest")

    for d in entries:
        manifest_file = d / "manifest.resolved.yaml"
        compose_file = d / "compose.agent.yml"

        runtime = "-"
        image = "-"
        port = "-"
        service = "-"
        has_manifest = "yes" if manifest_file.is_file() else "[red]no[/red]"

        if manifest_file.is_file():
            try:
                data = yaml.safe_load(manifest_file.read_text(encoding="utf-8"))
                spec = (data or {}).get("spec", {})
                runtime = spec.get("runtime", "-")
                deploy = spec.get("deploy", {})
                port = str(deploy.get("port", "-"))
            except Exception:  # noqa: BLE001
                pass

        if compose_file.is_file():
            try:
                cdata = yaml.safe_load(compose_file.read_text(encoding="utf-8"))
                services = (cdata or {}).get("services", {})
                if services:
                    svc_name = next(iter(services))
                    service = svc_name
                    image = services[svc_name].get("image", "-")
            except Exception:  # noqa: BLE001
                pass

        table.add_row(d.name, runtime, image, port, service, has_manifest)

    console.print(table)

from __future__ import annotations

from pathlib import Path

import httpx
import typer
from rich.console import Console
from rich.table import Table

project_app = typer.Typer(help="Manage workspace projects via the agent gateway.")
console = Console()

_DEFAULT_GATEWAY = "http://localhost:8000"
_GATEWAY_ENVVAR = "AGENTCTL_GATEWAY_URL"


def _gateway_opt() -> str:
    import os

    return os.environ.get(_GATEWAY_ENVVAR, _DEFAULT_GATEWAY)


@project_app.command("list")
def list_projects(
    gateway: str = typer.Option(
        _DEFAULT_GATEWAY,
        "--gateway",
        "-g",
        envvar=_GATEWAY_ENVVAR,
        help="Agent gateway base URL.",
    ),
) -> None:
    """List all projects registered on the gateway."""
    url = f"{gateway.rstrip('/')}/api/projects"
    try:
        resp = httpx.get(url, timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]HTTP {exc.response.status_code}: {exc.response.text[:200]}[/red]")
        raise typer.Exit(1) from exc
    except httpx.RequestError as exc:
        console.print(f"[red]Connection error: {exc}[/red]")
        raise typer.Exit(1) from exc

    projects = resp.json()
    if not projects:
        console.print("[dim]No projects found.[/dim]")
        return

    table = Table(title="Projects")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Default Agent")
    for p in projects:
        table.add_row(
            str(p.get("id", "")),
            p.get("name", ""),
            p.get("description", ""),
            p.get("default_agent") or "-",
        )
    console.print(table)


@project_app.command("create")
def create_project(
    name: str = typer.Argument(..., help="Project name."),
    description: str = typer.Option("", "--description", "-d", help="Optional description."),
    default_agent: str | None = typer.Option(
        None, "--agent", "-a", help="Default agent name for this project."
    ),
    gateway: str = typer.Option(
        _DEFAULT_GATEWAY,
        "--gateway",
        "-g",
        envvar=_GATEWAY_ENVVAR,
        help="Agent gateway base URL.",
    ),
) -> None:
    """Create a new project on the gateway."""
    url = f"{gateway.rstrip('/')}/api/projects"
    payload: dict = {"name": name, "description": description}
    if default_agent:
        payload["default_agent"] = default_agent

    try:
        resp = httpx.post(url, json=payload, timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]HTTP {exc.response.status_code}: {exc.response.text[:200]}[/red]")
        raise typer.Exit(1) from exc
    except httpx.RequestError as exc:
        console.print(f"[red]Connection error: {exc}[/red]")
        raise typer.Exit(1) from exc

    p = resp.json()
    console.print(f"[green]Created project[/green] [bold]{p['name']}[/bold] (id={p['id']})")


@project_app.command("get")
def get_project(
    project_id: int = typer.Argument(..., help="Project ID."),
    gateway: str = typer.Option(
        _DEFAULT_GATEWAY,
        "--gateway",
        "-g",
        envvar=_GATEWAY_ENVVAR,
        help="Agent gateway base URL.",
    ),
) -> None:
    """Get details of a project by ID."""
    url = f"{gateway.rstrip('/')}/api/projects/{project_id}"
    try:
        resp = httpx.get(url, timeout=10.0)
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]HTTP {exc.response.status_code}: {exc.response.text[:200]}[/red]")
        raise typer.Exit(1) from exc
    except httpx.RequestError as exc:
        console.print(f"[red]Connection error: {exc}[/red]")
        raise typer.Exit(1) from exc

    p = resp.json()
    console.print(f"[bold]id[/bold]: {p['id']}")
    console.print(f"[bold]name[/bold]: {p['name']}")
    console.print(f"[bold]description[/bold]: {p.get('description', '')}")
    console.print(f"[bold]default_agent[/bold]: {p.get('default_agent') or '-'}")


@project_app.command("workspace")
def workspace_info(
    workspace: Path = typer.Option(
        Path(".workspace"),
        "--path",
        "-p",
        help="Path to the workspace folder.",
    ),
) -> None:
    """Show files currently in the workspace folder."""
    if not workspace.exists():
        console.print(f"[yellow]Workspace folder does not exist: {workspace}[/yellow]")
        console.print("[dim]Create it with: mkdir .workspace[/dim]")
        return

    files = sorted(workspace.rglob("*"))
    file_list = [f for f in files if f.is_file()]
    if not file_list:
        console.print(f"[dim]Workspace is empty: {workspace}[/dim]")
        return

    table = Table(title=f"Workspace: {workspace}")
    table.add_column("Path", style="cyan")
    table.add_column("Size", justify="right", style="dim")
    for f in file_list:
        rel = f.relative_to(workspace)
        size = f.stat().st_size
        table.add_row(str(rel), f"{size:,} B")
    console.print(table)


@project_app.command("reindex")
def reindex_workspace(
    gateway: str = typer.Option(
        _DEFAULT_GATEWAY,
        "--gateway",
        "-g",
        envvar=_GATEWAY_ENVVAR,
        help="Agent gateway base URL.",
    ),
) -> None:
    """Trigger a workspace re-index on the gateway (refreshes ChromaDB embeddings)."""
    url = f"{gateway.rstrip('/')}/api/workspace/reindex"
    try:
        resp = httpx.post(url, timeout=30.0)
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]HTTP {exc.response.status_code}: {exc.response.text[:200]}[/red]")
        raise typer.Exit(1) from exc
    except httpx.RequestError as exc:
        console.print(f"[red]Connection error: {exc}[/red]")
        raise typer.Exit(1) from exc

    data = resp.json()
    console.print(f"[green]Reindexed[/green] {data.get('indexed', 0)} workspace files.")

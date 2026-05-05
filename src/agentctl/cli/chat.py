from __future__ import annotations

import re
import sys
from pathlib import Path

import httpx
from rich.console import Console
from rich.markdown import Markdown

console = Console()

# Matches @word or @path/to/file.ext — used to resolve file references in messages.
_FILE_REF_RE = re.compile(r"@([\w./\-]+\.\w+)")
# Matches bare @agentname (no dot/slash, not a filename pattern).
_AGENT_REF_RE = re.compile(r"@([a-z][a-z0-9-]*)\b")


def _strip_at(name: str) -> str:
    return name.lstrip("@")


def _expand_message(message: str, workspace: Path) -> str:
    """Replace @file.ext references with file contents from the workspace folder."""

    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        rel = m.group(1)
        # Prevent path traversal by ensuring the resolved path stays within workspace
        try:
            candidate = (workspace / rel).resolve()
            workspace_resolved = workspace.resolve()
            candidate.relative_to(workspace_resolved)  # raises ValueError if outside
        except ValueError:
            console.print(f"[yellow]Warning: file reference outside workspace rejected: {rel}[/yellow]")
            return m.group(0)
        if candidate.is_file():
            content = candidate.read_text(encoding="utf-8")
            return f"\n\n--- {rel} ---\n{content}\n--- end {rel} ---\n\n"
        console.print(f"[yellow]Warning: workspace file not found: {candidate}[/yellow]")
        return m.group(0)

    return _FILE_REF_RE.sub(_replace, message)


def _send_message(
    *,
    agent_name: str,
    message: str,
    gateway_url: str,
    stream: bool,
) -> None:
    url_base = gateway_url.rstrip("/")
    payload = {"agent_lookup": agent_name, "message": message}

    if stream:
        url = f"{url_base}/api/invoke/stream"
        try:
            with httpx.Client(timeout=120.0) as client:
                with client.stream("POST", url, json=payload) as resp:
                    if resp.status_code == 404:
                        console.print(f"[red]Agent {agent_name!r} not found (404).[/red]")
                        return
                    resp.raise_for_status()
                    console.print(f"\n[bold green]{agent_name}[/bold green]: ", end="")
                    for line in resp.iter_lines():
                        if line.startswith("data: "):
                            chunk = line[6:]
                            if chunk == "[DONE]":
                                break
                            if chunk.startswith("[ERROR]"):
                                console.print(f"\n[red]{chunk}[/red]")
                                break
                            console.print(chunk, end="", highlight=False)
                    console.print()
        except httpx.HTTPStatusError as exc:
            console.print(f"[red]HTTP {exc.response.status_code}: {exc.response.text[:200]}[/red]")
        except httpx.RequestError as exc:
            console.print(f"[red]Connection error: {exc}[/red]")
    else:
        url = f"{url_base}/api/invoke"
        try:
            with httpx.Client(timeout=120.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 404:
                    console.print(f"[red]Agent {agent_name!r} not found (404).[/red]")
                    return
                resp.raise_for_status()
                data = resp.json()
                output = data.get("output", "")
                console.print(f"\n[bold green]{agent_name}[/bold green]:")
                console.print(Markdown(output))
        except httpx.HTTPStatusError as exc:
            console.print(f"[red]HTTP {exc.response.status_code}: {exc.response.text[:200]}[/red]")
        except httpx.RequestError as exc:
            console.print(f"[red]Connection error: {exc}[/red]")


def run_chat(
    *,
    agent: str,
    message: str | None,
    gateway_url: str,
    workspace: Path,
    stream: bool,
) -> None:
    agent_name = _strip_at(agent)

    if message is not None:
        expanded = _expand_message(message, workspace)
        _send_message(
            agent_name=agent_name,
            message=expanded,
            gateway_url=gateway_url,
            stream=stream,
        )
        return

    # Interactive mode
    console.print(
        f"[bold]Chatting with [green]{agent_name}[/green][/bold] "
        f"(gateway: {gateway_url})\n"
        "Type your message and press Enter. Use [bold]@filename[/bold] to include workspace files.\n"
        "Commands: [bold]/exit[/bold] or [bold]/quit[/bold] to leave.\n"
    )

    while True:
        try:
            raw = console.input("[cyan]you[/cyan]: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not raw:
            continue
        if raw.lower() in ("/exit", "/quit"):
            console.print("[dim]Goodbye.[/dim]")
            break

        # Support switching agents mid-session: /agent <name>
        if raw.startswith("/agent "):
            agent_name = _strip_at(raw.split(maxsplit=1)[1].strip())
            console.print(f"[dim]Switched to agent: {agent_name}[/dim]")
            continue

        expanded = _expand_message(raw, workspace)
        _send_message(
            agent_name=agent_name,
            message=expanded,
            gateway_url=gateway_url,
            stream=stream,
        )

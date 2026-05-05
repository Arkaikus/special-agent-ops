from __future__ import annotations

import re
import subprocess
from pathlib import Path

import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

# Matches @word or @path/to/file.ext — used to resolve file references in messages.
_FILE_REF_RE = re.compile(r"@([\w./\-]+\.\w+)")
# Matches bare @agentname (no dot/slash, not a filename pattern).
_AGENT_REF_RE = re.compile(r"@([a-z][a-z0-9-]*)\b")

# CLI commands dispatchable from chat via /command
_CLI_COMMANDS: dict[str, list[str]] = {
    "up":     ["agentctl", "up"],
    "stop":   ["agentctl", "stop"],
    "down":   ["agentctl", "down"],
    "list":   ["agentctl", "list"],
    "doctor": ["agentctl", "doctor"],
    "logs":   ["agentctl", "logs"],
}


def _strip_at(name: str) -> str:
    return name.lstrip("@")


def _expand_message(message: str, workspace: Path) -> str:
    """Replace @file.ext references with file contents from the workspace folder."""

    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        rel = m.group(1)
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
                    # Print live chunks then re-render full response as Markdown panel
                    console.print(f"\n[bold green]{agent_name}[/bold green] (streaming):", end="")
                    chunks: list[str] = []
                    for line in resp.iter_lines():
                        if line.startswith("data: "):
                            chunk = line[6:]
                            if chunk == "[DONE]":
                                break
                            if chunk.startswith("[ERROR]"):
                                console.print(f"\n[red]{chunk}[/red]")
                                return
                            if chunk.startswith("[TOOL_CALL] "):
                                # Tool invocation event — show as dim annotation, not part of response
                                console.print(
                                    f"\n[dim yellow]  ⚙ {chunk.removeprefix('[TOOL_CALL] ')}[/dim yellow]",
                                    end="",
                                )
                                continue
                            # Restore newlines escaped for SSE transport
                            decoded = chunk.replace("\\n", "\n")
                            console.print(decoded, end="", highlight=False)
                            chunks.append(decoded)
                    console.print()
                    full = "".join(chunks)
                    if full.strip():
                        console.print(
                            Panel(
                                Markdown(full),
                                border_style="green",
                                title=f"[bold green]{agent_name}[/bold green]",
                                expand=False,
                            )
                        )
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
                console.print(
                    Panel(
                        Markdown(output),
                        border_style="green",
                        title=f"[bold green]{agent_name}[/bold green]",
                        expand=False,
                    )
                )
        except httpx.HTTPStatusError as exc:
            console.print(f"[red]HTTP {exc.response.status_code}: {exc.response.text[:200]}[/red]")
        except httpx.RequestError as exc:
            console.print(f"[red]Connection error: {exc}[/red]")


def _handle_slash_command(raw: str, agent_name: str | None) -> tuple[bool, str | None]:
    """Process a /command line. Returns (handled, new_agent_name | None)."""
    parts = raw.split()
    cmd = parts[0].lstrip("/")

    # /exit /quit
    if cmd in ("exit", "quit"):
        console.print("[dim]Goodbye.[/dim]")
        raise SystemExit(0)

    # /help
    if cmd == "help":
        console.print(
            Panel(
                "\n".join([
                    "[bold]Agent routing[/bold]",
                    "  [cyan]/<agentname>[/cyan]           switch active agent (e.g. /architect)",
                    "  [cyan]/agent <name>[/cyan]          switch active agent",
                    "  [cyan]@agentname <msg>[/cyan]       send one-shot message to agent",
                    "",
                    "[bold]CLI commands[/bold]",
                    "  [cyan]/up [agent][/cyan]            agentctl up",
                    "  [cyan]/stop [agent][/cyan]          agentctl stop",
                    "  [cyan]/down [agent][/cyan]          agentctl down",
                    "  [cyan]/list[/cyan]                  agentctl list",
                    "  [cyan]/logs <agent>[/cyan]          agentctl logs",
                    "  [cyan]/doctor[/cyan]                agentctl doctor",
                    "",
                    "[bold]Other[/bold]",
                    "  [cyan]@filename.ext[/cyan]          inline workspace file contents",
                    "  [cyan]/exit[/cyan]  [cyan]/quit[/cyan]          leave chat",
                ]),
                title="[bold]agentctl chat — help[/bold]",
                border_style="dim",
            )
        )
        return True, None

    # /agent <name>
    if cmd == "agent" and len(parts) >= 2:
        new_agent = _strip_at(parts[1])
        console.print(f"[dim]Switched to agent: {new_agent}[/dim]")
        return True, new_agent

    # /up, /stop, /down, /list, /logs, /doctor → delegate to agentctl subprocess
    if cmd in _CLI_COMMANDS:
        base_cmd = _CLI_COMMANDS[cmd]
        extra = parts[1:]  # optional agent name / extra flags
        full_cmd = base_cmd + extra
        console.print(f"[dim]$ {' '.join(full_cmd)}[/dim]")
        try:
            subprocess.run(full_cmd, check=False)
        except FileNotFoundError:
            console.print("[red]agentctl not found in PATH[/red]")
        return True, None

    # /somename — treat as agent switch if it looks like a valid agent name
    if re.fullmatch(r"[a-z][a-z0-9-]*", cmd):
        console.print(f"[dim]Switched to agent: {cmd}[/dim]")
        return True, cmd

    console.print(f"[yellow]Unknown command: {raw!r}. Type /help for available commands.[/yellow]")
    return True, None


def run_chat(
    *,
    agent: str | None,
    message: str | None,
    gateway_url: str,
    workspace: Path,
    stream: bool,
) -> None:
    agent_name: str | None = _strip_at(agent) if agent else None

    # One-shot non-interactive mode
    if message is not None:
        if not agent_name:
            console.print(
                "[red]Specify an agent name when passing a message directly "
                "(e.g. agentctl chat architect 'hello').[/red]"
            )
            raise SystemExit(1)
        expanded = _expand_message(message, workspace)
        _send_message(
            agent_name=agent_name,
            message=expanded,
            gateway_url=gateway_url,
            stream=stream,
        )
        return

    # Interactive general-chat mode
    if agent_name:
        subtitle = f"Active agent: [green]{agent_name}[/green] · gateway: {gateway_url}"
    else:
        subtitle = (
            f"No active agent — use [cyan]/<agentname>[/cyan] to select one · gateway: {gateway_url}"
        )

    console.print(
        Panel(
            "\n".join([
                subtitle,
                "Use [bold]@filename[/bold] to inline workspace files.",
                "Type [bold]/help[/bold] for slash commands, [bold]/exit[/bold] to quit.",
            ]),
            title="[bold]agentctl chat[/bold]",
            border_style="cyan",
        )
    )

    while True:
        try:
            prompt_label = f"[cyan]{agent_name or 'you'}[/cyan]"
            raw = console.input(f"{prompt_label}: ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not raw:
            continue

        # ── Slash commands ────────────────────────────────────────────────────
        if raw.startswith("/"):
            handled, new_agent = _handle_slash_command(raw, agent_name)
            if new_agent is not None:
                agent_name = new_agent
            continue

        # ── Inline @agentname routing: "@architect explain this" ─────────────
        inline_agent_match = _AGENT_REF_RE.match(raw)
        if inline_agent_match and not _FILE_REF_RE.match(raw):
            routed_agent = inline_agent_match.group(1)
            msg_body = raw[inline_agent_match.end():].strip()
            if msg_body:
                expanded = _expand_message(msg_body, workspace)
                _send_message(
                    agent_name=routed_agent,
                    message=expanded,
                    gateway_url=gateway_url,
                    stream=stream,
                )
                continue
            # @agentname with no body → switch agent
            console.print(f"[dim]Switched to agent: {routed_agent}[/dim]")
            agent_name = routed_agent
            continue

        # ── Regular message to active agent ──────────────────────────────────
        if not agent_name:
            console.print(
                "[yellow]No agent selected. "
                "Use [cyan]/<agentname>[/cyan] or [cyan]@agentname <message>[/cyan] "
                "to direct your message.[/yellow]"
            )
            continue

        expanded = _expand_message(raw, workspace)
        _send_message(
            agent_name=agent_name,
            message=expanded,
            gateway_url=gateway_url,
            stream=stream,
        )

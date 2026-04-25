"""Sandboxed workspace filesystem tools (generated alongside server.py)."""
from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path

WORKSPACE = Path(os.environ.get("WORKSPACE_ROOT", "/workspace")).resolve()

MAX_READ_BYTES = 512_000
MAX_GREP_FILES = 200
BASH_TIMEOUT_SEC = 45.0


def _under_workspace(p: Path) -> bool:
    try:
        p.resolve().relative_to(WORKSPACE)
        return True
    except ValueError:
        return False


def _safe_path(rel: str) -> Path:
    if rel.startswith("/") or ".." in Path(rel).parts:
        raise ValueError("path must be relative to workspace")
    out = (WORKSPACE / rel).resolve()
    if not _under_workspace(out):
        raise ValueError("path escapes workspace")
    return out


async def tool_ls(path: str = ".") -> str:
    """List files and directories under a path relative to the workspace root."""
    p = _safe_path(path) if path not in (".", "") else WORKSPACE
    if not p.exists():
        return f"not found: {path}"
    if p.is_file():
        return str(p.relative_to(WORKSPACE))
    lines: list[str] = []
    for child in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        kind = "d" if child.is_dir() else "f"
        lines.append(f"{kind} {child.name}")
    return "\n".join(lines) if lines else "(empty)"


async def tool_grep(pattern: str, path: str = ".", glob_pattern: str = "**/*") -> str:
    """Search text files under path for a regex pattern (bounded)."""
    try:
        rx = re.compile(pattern)
    except re.error as e:
        return f"invalid regex: {e}"
    root = _safe_path(path) if path not in (".", "") else WORKSPACE
    if not root.exists():
        return f"not found: {path}"
    matches: list[str] = []
    n_files = 0
    for fp in root.rglob("*") if glob_pattern == "**/*" else root.glob(glob_pattern):
        if not fp.is_file():
            continue
        n_files += 1
        if n_files > MAX_GREP_FILES:
            matches.append(f"(stopped after {MAX_GREP_FILES} files)")
            break
        try:
            data = fp.read_bytes()[:MAX_READ_BYTES]
            text = data.decode("utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if rx.search(line):
                rel = fp.relative_to(WORKSPACE)
                matches.append(f"{rel}:{i}:{line[:500]}")
                if len(matches) >= 500:
                    return "\n".join(matches) + "\n(truncated)"
    return "\n".join(matches) if matches else "(no matches)"


async def tool_glob(pattern: str) -> str:
    """Glob files relative to workspace (e.g. '*.py', 'src/**/*.ts')."""
    if pattern.startswith("/") or ".." in pattern:
        raise ValueError("invalid glob pattern")
    paths = sorted(
        {str(p.relative_to(WORKSPACE)) for p in WORKSPACE.glob(pattern) if _under_workspace(p.resolve())}
    )
    return "\n".join(paths[:500]) + ("\n(truncated)" if len(paths) > 500 else "")


async def tool_edit(path: str, old_text: str | None, new_text: str) -> str:
    """Replace old_text with new_text in a file, or write new_text if old_text is empty (full replace)."""
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if old_text is None or old_text == "":
        p.write_text(new_text, encoding="utf-8")
        return f"wrote {path}"
    cur = p.read_text(encoding="utf-8", errors="replace")
    if old_text not in cur:
        return "old_text not found in file"
    p.write_text(cur.replace(old_text, new_text, 1), encoding="utf-8")
    return f"updated {path}"


async def tool_bash(cmd: str) -> str:
    """Run a shell command with cwd=workspace (use with care)."""
    proc = await asyncio.create_subprocess_shell(
        cmd,
        cwd=WORKSPACE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env={**os.environ, "LC_ALL": "C.UTF-8"},
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=BASH_TIMEOUT_SEC)
    except TimeoutError:
        proc.kill()
        return "timeout"
    text = out.decode("utf-8", errors="replace")
    if len(text) > 20_000:
        text = text[:20_000] + "\n(truncated)"
    return f"exit {proc.returncode}\n{text}"

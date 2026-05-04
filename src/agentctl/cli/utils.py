from __future__ import annotations

from pathlib import Path

_REPO_MARKERS = ("docker-compose.yml", ".git", "pyproject.toml")


def find_repo_root(start: Path | None = None) -> Path:
    """Walk up from *start* (default: cwd) until a repo marker is found.

    Raises SystemExit if no marker is found before the filesystem root.
    """
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if any((candidate / m).exists() for m in _REPO_MARKERS):
            return candidate
    raise SystemExit(
        f"Could not find repo root (looked for {_REPO_MARKERS}) "
        f"starting from {current}"
    )

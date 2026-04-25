from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import Iterable


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text_atomic(target: Path, content: str, dry_run: bool) -> None:
    if dry_run:
        return
    ensure_dir(target.parent)
    fd, tmp = tempfile.mkstemp(prefix=target.name, dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass


def sync_tree(
    source_dir: Path,
    dest_dir: Path,
    *,
    dry_run: bool,
    ignore: Iterable[str] = (),
) -> None:
    """Copy files from source_dir into dest_dir (for skills)."""
    ignore_set = set(ignore)
    if not source_dir.is_dir():
        return
    for root, dirs, files in os.walk(source_dir):
        dirs[:] = [d for d in dirs if d not in ignore_set]
        rel = Path(root).relative_to(source_dir)
        for name in files:
            if name in ignore_set:
                continue
            src = Path(root) / name
            dst = dest_dir / rel / name
            if dry_run:
                continue
            ensure_dir(dst.parent)
            shutil.copy2(src, dst)


def clear_output_dir(output_root: Path, *, dry_run: bool, force: bool) -> None:
    if not output_root.exists():
        return
    if not force:
        return
    if dry_run:
        return
    shutil.rmtree(output_root)

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from agentctl.codegen import CodegenContext, run_codegen_for_runtime
from agentctl.codegen.writer import clear_output_dir, ensure_dir, sync_tree, write_text_atomic
from agentctl.manifest.io import dump_manifest, load_manifest_from_path
from agentctl.deploy.templates import (
    render_agent_compose,
    render_dockerfile_python,
    render_dockerfile_rust,
)

console = Console()


def run_apply(manifest_path: Path, *, dry_run: bool, force: bool) -> None:
    manifest = load_manifest_from_path(manifest_path)
    repo_root = Path.cwd()
    ctx = CodegenContext.from_manifest(manifest, repo_root)

    if ctx.output_root.exists() and not force and not dry_run:
        console.print(
            f"[yellow]Output {ctx.output_root} exists; use --force to overwrite.[/yellow]"
        )
        raise SystemExit(1)

    clear_output_dir(ctx.output_root, dry_run=dry_run, force=force)
    if not dry_run:
        ensure_dir(ctx.output_root)

    # Skills: copy local paths relative to manifest file directory
    base = manifest_path.parent
    skills_dest = ctx.output_root / "skills"
    for skill in manifest.spec.skills:
        if skill.path:
            src = (base / skill.path).resolve()
            if not src.exists():
                raise SystemExit(f"skill path not found: {src}")
            if src.is_file():
                if not dry_run:
                    ensure_dir(skills_dest)
                    write_text_atomic(skills_dest / src.name, src.read_text(encoding="utf-8"), dry_run=False)
            else:
                sync_tree(src, skills_dest / src.name, dry_run=dry_run)
        elif skill.inline_prompt:
            if not dry_run:
                ensure_dir(skills_dest)
                name = "inline-prompt.md"
                write_text_atomic(skills_dest / name, skill.inline_prompt, dry_run=False)
        elif skill.git:
            console.print(
                f"[yellow]Skipping git skill (not cloned in MVP): {skill.git}[/yellow]"
            )

    paths = run_codegen_for_runtime(ctx, dry_run=dry_run)

    resolved = ctx.output_root / "manifest.resolved.yaml"
    write_text_atomic(resolved, dump_manifest(manifest), dry_run)

    if ctx.manifest.spec.runtime == "swarm-rs":
        df = render_dockerfile_rust(ctx)
    else:
        df = render_dockerfile_python(ctx)
    write_text_atomic(ctx.output_root / "Dockerfile", df, dry_run)

    compose_extra = render_agent_compose(ctx)
    write_text_atomic(ctx.output_root / "compose.agent.yml", compose_extra, dry_run)

    console.print(f"[green]Wrote[/green] {len(paths) + 3} artifacts under {ctx.output_root}")
    if dry_run:
        console.print("[blue]Dry run: no files written.[/blue]")

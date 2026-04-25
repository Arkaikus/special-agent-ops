from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from agentctl.codegen.context import CodegenContext
from agentctl.codegen.writer import write_text_atomic


def _env() -> Environment:
    root = Path(__file__).parent / "templates"
    return Environment(
        loader=FileSystemLoader(str(root)),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def generate_swarm_rs(ctx: CodegenContext, *, dry_run: bool) -> list[Path]:
    written: list[Path] = []
    root = ctx.output_root / "rust"
    env = _env()
    name = ctx.agent_name.replace("-", "_")
    for fname, tmpl_name in [
        ("Cargo.toml", "Cargo.toml.j2"),
        ("src/main.rs", "main.rs.j2"),
        ("config.toml", "config.toml.j2"),
        ("README.md", "README.md.j2"),
    ]:
        tpl = env.get_template(tmpl_name)
        content = tpl.render(
            agent_name=ctx.agent_name,
            crate_name=name,
            port=ctx.manifest.spec.deploy.port,
        )
        out = root / fname
        write_text_atomic(out, content, dry_run)
        written.append(out)
    return written

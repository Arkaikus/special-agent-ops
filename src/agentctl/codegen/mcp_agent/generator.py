from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from agentctl.codegen.context import CodegenContext
from agentctl.codegen.writer import write_text_atomic
from agentctl.codegen.pydantic_ai.generator import generate_pydantic_ai


def _mcp_env() -> Environment:
    root = Path(__file__).parent / "templates"
    return Environment(
        loader=FileSystemLoader(str(root)),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def generate_mcp_agent(ctx: CodegenContext, *, dry_run: bool) -> list[Path]:
    """MCP-forward runtime: pydantic-ai agent with toolsets + optional Redis fan-out hook."""
    paths = generate_pydantic_ai(ctx, dry_run=dry_run)
    env = _mcp_env()
    hook = env.get_template("redis_hook.py.j2").render(agent_name=ctx.agent_name)
    out = ctx.output_root / "python" / "redis_hook.py"
    write_text_atomic(out, hook, dry_run)
    paths.append(out)
    readme = env.get_template("README.md.j2").render(agent_name=ctx.agent_name)
    write_text_atomic(ctx.output_root / "python" / "MCP_RUNTIME.md", readme, dry_run)
    paths.append(ctx.output_root / "python" / "MCP_RUNTIME.md")
    return paths

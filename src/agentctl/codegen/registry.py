from __future__ import annotations

from pathlib import Path

from agentctl.codegen.context import CodegenContext
from agentctl.codegen.mcp_agent import generate_mcp_agent
from agentctl.codegen.pydantic_ai import generate_pydantic_ai
from agentctl.codegen.swarm_rs import generate_swarm_rs


def run_codegen_for_runtime(ctx: CodegenContext, *, dry_run: bool) -> list[Path]:
    runtime = ctx.manifest.spec.runtime
    if runtime == "pydantic-ai":
        return generate_pydantic_ai(ctx, dry_run=dry_run)
    if runtime == "mcp-agent":
        return generate_mcp_agent(ctx, dry_run=dry_run)
    if runtime == "swarm-rs":
        return generate_swarm_rs(ctx, dry_run=dry_run)
    raise ValueError(f"unknown runtime: {runtime}")

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from agentctl.codegen.context import CodegenContext
from agentctl.codegen.writer import write_text_atomic
from agentctl.manifest.v1 import (
    AgentManifest,
    ModelAnthropic,
    ModelOllama,
    ModelOpenAICompatible,
)


def _template_env() -> Environment:
    root = Path(__file__).parent / "templates"
    return Environment(
        loader=FileSystemLoader(str(root)),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def _model_context(manifest: AgentManifest) -> dict[str, Any]:
    m = manifest.spec.model
    if isinstance(m, ModelAnthropic):
        return {
            "provider": "anthropic",
            "model_id": m.model_id,
            "api_key_env": m.api_key_env,
            "temperature": m.temperature,
            "base_url": None,
        }
    if isinstance(m, ModelOllama):
        return {
            "provider": "ollama",
            "model_id": m.model_id,
            "api_key_env": m.api_key_env or "",
            "temperature": m.temperature,
            "base_url": m.base_url,
        }
    if isinstance(m, ModelOpenAICompatible):
        return {
            "provider": "openai_compatible",
            "model_id": m.model_id,
            "api_key_env": m.api_key_env or "",
            "temperature": m.temperature,
            "base_url": m.base_url,
        }
    raise TypeError(f"unsupported model config: {type(m)}")


def generate_pydantic_ai(ctx: CodegenContext, *, dry_run: bool) -> list[Path]:
    env = _template_env()
    written: list[Path] = []
    py_root = ctx.output_root / "python"
    system_prompt = ctx.manifest.spec.prompts.get("system") or "You are a helpful assistant."
    mcp_servers_literal = repr(
        [s.model_dump(mode="python", by_alias=True) for s in ctx.manifest.spec.mcp_servers]
    )
    skill_paths = [s.path for s in ctx.manifest.spec.skills if s.path]

    ctx_vars = {
        "agent_name": ctx.agent_name,
        "port": ctx.manifest.spec.deploy.port,
        "system_prompt": system_prompt,
        "model": _model_context(ctx.manifest),
        "mcp_servers_literal": mcp_servers_literal,
        "skill_paths": skill_paths,
        "has_mcp": bool(ctx.manifest.spec.mcp_servers),
    }

    for name in ("server.py", "pyproject.toml", "README.md"):
        tpl = env.get_template(f"{name}.j2")
        content = tpl.render(**ctx_vars)
        out = py_root / name
        write_text_atomic(out, content, dry_run)
        written.append(out)

    return written

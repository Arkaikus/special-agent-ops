from __future__ import annotations

import shutil
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
    effective_fs_allow,
    workspace_root_for_spec,
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


def _workspace_tools_source() -> Path:
    return Path(__file__).parent / "templates" / "workspace_tools.py"


def generate_pydantic_ai(ctx: CodegenContext, *, dry_run: bool) -> list[Path]:
    env = _template_env()
    written: list[Path] = []
    py_root = ctx.output_root / "python"
    system_prompt = ctx.manifest.spec.prompts.get("system") or "You are a helpful assistant."
    mcp_servers_literal = repr(
        [s.model_dump(mode="python", by_alias=True) for s in ctx.manifest.spec.mcp_servers]
    )
    skill_paths = [s.path for s in ctx.manifest.spec.skills if s.path]

    fs_allow = effective_fs_allow(ctx.manifest.spec.fs_tools)
    has_fs = fs_allow is not None
    wr = workspace_root_for_spec(ctx.manifest.spec) or "/workspace"
    fs_allow_literal = repr(list(fs_allow) if fs_allow else [])

    ctx_vars = {
        "agent_name": ctx.agent_name,
        "port": ctx.manifest.spec.deploy.port,
        "system_prompt": system_prompt,
        "model": _model_context(ctx.manifest),
        "mcp_servers_literal": mcp_servers_literal,
        "skill_paths": skill_paths,
        "has_mcp": bool(ctx.manifest.spec.mcp_servers),
        "has_fs": has_fs,
        "fs_allow_literal": fs_allow_literal,
        "workspace_root": wr,
    }

    for name in ("server.py", "pyproject.toml", "README.md"):
        tpl = env.get_template(f"{name}.j2")
        content = tpl.render(**ctx_vars)
        out = py_root / name
        write_text_atomic(out, content, dry_run)
        written.append(out)

    if has_fs and not dry_run:
        src = _workspace_tools_source()
        dst = py_root / "workspace_tools.py"
        ensure_dir = dst.parent
        ensure_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        written.append(dst)
    elif has_fs and dry_run:
        written.append(py_root / "workspace_tools.py")

    return written

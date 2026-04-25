from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from agentctl.codegen.context import CodegenContext


def _env() -> Environment:
    root = Path(__file__).parent / "templates"
    return Environment(
        loader=FileSystemLoader(str(root)),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_dockerfile_python(ctx: CodegenContext) -> str:
    port = ctx.manifest.spec.deploy.port
    tpl = _env().get_template("Dockerfile.python.j2")
    return tpl.render(agent_name=ctx.agent_name, port=port)


def render_dockerfile_rust(ctx: CodegenContext) -> str:
    port = ctx.manifest.spec.deploy.port
    crate_name = ctx.agent_name.replace("-", "_")
    tpl = _env().get_template("Dockerfile.rust.j2")
    return tpl.render(crate_name=crate_name, port=port)


def render_agent_compose(ctx: CodegenContext) -> str:
    service = ctx.manifest.spec.deploy.compose_service or ctx.agent_name
    port = ctx.manifest.spec.deploy.port
    image = ctx.manifest.spec.deploy.image or f"agentctl/{ctx.agent_name}:local"
    tpl = _env().get_template("compose.agent.yml.j2")
    return tpl.render(
        service_name=service,
        agent_name=ctx.agent_name,
        port=port,
        image=image,
    )

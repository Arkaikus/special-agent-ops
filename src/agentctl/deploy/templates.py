from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from agentctl.codegen.context import CodegenContext
from agentctl.manifest.v1 import effective_fs_allow, workspace_root_for_spec


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
    wr = workspace_root_for_spec(ctx.manifest.spec)
    has_w = bool(ctx.manifest.spec.workspaces.volumes) or (
        effective_fs_allow(ctx.manifest.spec.fs_tools) is not None
    )
    tpl = _env().get_template("Dockerfile.python.j2")
    return tpl.render(
        agent_name=ctx.agent_name,
        port=port,
        has_workspace=has_w and wr is not None,
        workspace_root=wr or "/workspace",
    )


def render_dockerfile_rust(ctx: CodegenContext) -> str:
    port = ctx.manifest.spec.deploy.port
    crate_name = ctx.agent_name.replace("-", "_")
    tpl = _env().get_template("Dockerfile.rust.j2")
    return tpl.render(crate_name=crate_name, port=port)


def render_agent_compose(ctx: CodegenContext) -> str:
    service = ctx.manifest.spec.deploy.compose_service or ctx.agent_name
    port = ctx.manifest.spec.deploy.port
    image = ctx.manifest.spec.deploy.image or f"agentctl/{ctx.agent_name}:local"
    wr = workspace_root_for_spec(ctx.manifest.spec)
    has_w = bool(ctx.manifest.spec.workspaces.volumes) or (
        effective_fs_allow(ctx.manifest.spec.fs_tools) is not None
    )

    service_volumes: list[str] = []
    named: list[str] = []
    for v in ctx.manifest.spec.workspaces.volumes:
        if v.name is not None:
            line = f"{v.name}:{v.target}"
            if v.read_only:
                line += ":ro"
            service_volumes.append(line)
            if v.name not in named:
                named.append(v.name)
        elif v.host_path is not None:
            line = f"{v.host_path}:{v.target}"
            if v.read_only:
                line += ":ro"
            service_volumes.append(line)

    extra_hosts = list(ctx.manifest.spec.deploy.extra_hosts)
    tpl = _env().get_template("compose.agent.yml.j2")
    return tpl.render(
        service_name=service,
        agent_name=ctx.agent_name,
        port=port,
        image=image,
        service_volumes=service_volumes,
        named_volumes=named,
        extra_hosts=extra_hosts,
        workspace_root=wr or "/workspace",
        has_workspace=has_w and wr is not None,
    )

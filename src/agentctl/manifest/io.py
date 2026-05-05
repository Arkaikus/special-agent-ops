from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from agentctl.manifest.v1 import (
    API_VERSION_V1,
    AgentManifest,
    AgentSpec,
    DeployConfig,
    FsToolsConfig,
    FsToolName,
    McpServer,
    Metadata,
    ModelConfig,
    SkillRef,
    VolumeMount,
    WorkspacesConfig,
)

# Matches `---\n<yaml>\n---` at the top of a markdown file.
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)


def _load_md_frontmatter(path: Path) -> AgentManifest:
    """Parse an agent definition written as markdown with YAML frontmatter.

    Frontmatter keys accepted:
      name, description, runtime, model, volumes, tools, mcp, skills, deploy

    The markdown body (after the closing ``---``) becomes ``spec.prompts.system``.
    """
    raw = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(raw)
    if not m:
        raise ValueError(
            f"markdown manifest {path} must start with a YAML frontmatter block (--- ... ---)"
        )
    fm_text, body = m.group(1), m.group(2).strip()

    try:
        fm: Any = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        raise ValueError(f"invalid YAML frontmatter in {path}: {e}") from e

    if not isinstance(fm, dict):
        raise ValueError(f"frontmatter must be a YAML mapping in {path}")

    name: str = fm.get("name", "")
    description: str | None = fm.get("description")
    runtime = fm.get("runtime", "pydantic-ai")

    # -- model ----------------------------------------------------------------
    raw_model = fm.get("model")
    if not raw_model:
        raise ValueError(f"frontmatter must contain a 'model' key in {path}")
    try:
        model: ModelConfig = _parse_model(raw_model)  # type: ignore[assignment]
    except Exception as exc:
        raise ValueError(f"invalid model config in {path}: {exc}") from exc

    # -- volumes --------------------------------------------------------------
    raw_volumes: list[dict] = fm.get("volumes", [])
    volumes = [_parse_volume(v) for v in raw_volumes]

    # -- tools (fs_tools) -----------------------------------------------------
    raw_tools: list[str] = fm.get("tools", [])
    fs_tools: FsToolsConfig | None = None
    if raw_tools:
        fs_tools = FsToolsConfig(enabled=True, allow=raw_tools)  # type: ignore[arg-type]

    # -- mcp servers ----------------------------------------------------------
    raw_mcp: list[dict] = fm.get("mcp", [])
    mcp_servers = [McpServer.model_validate(s) for s in raw_mcp]

    # -- skills ---------------------------------------------------------------
    raw_skills: list[Any] = fm.get("skills", [])
    skills: list[SkillRef] = []
    for s in raw_skills:
        if isinstance(s, str):
            skills.append(SkillRef(path=s))
        elif isinstance(s, dict):
            skills.append(SkillRef.model_validate(s))

    # -- deploy ---------------------------------------------------------------
    raw_deploy: dict = fm.get("deploy", {})
    deploy = DeployConfig.model_validate(raw_deploy) if raw_deploy else DeployConfig()

    # -- workspace ---------------------------------------------------------------
    # Automatically mount .workspace when volumes are declared but no explicit
    # workspace folder is provided.
    workspaces = WorkspacesConfig(volumes=volumes)

    # -- system prompt from body -----------------------------------------------
    prompts: dict[str, str] = {}
    if body:
        prompts["system"] = body

    spec = AgentSpec(
        runtime=runtime,  # type: ignore[arg-type]
        model=model,
        mcp_servers=mcp_servers,
        skills=skills,
        prompts=prompts,
        deploy=deploy,
        workspaces=workspaces,
        fs_tools=fs_tools,
    )
    metadata = Metadata(name=name, description=description)
    return AgentManifest(
        api_version=API_VERSION_V1,
        metadata=metadata,
        spec=spec,
    )


def _parse_model(raw: Any) -> Any:
    """Delegate to Pydantic discriminated union for model config."""
    from agentctl.manifest.v1 import ModelAnthropic, ModelOllama, ModelOpenAICompatible

    if not isinstance(raw, dict):
        raise ValueError("model must be a mapping")
    t = raw.get("type", "")
    mapping = {
        "anthropic": ModelAnthropic,
        "ollama": ModelOllama,
        "openai_compatible": ModelOpenAICompatible,
    }
    cls = mapping.get(t)
    if cls is None:
        raise ValueError(f"unknown model type {t!r}")
    return cls.model_validate(raw)


def _parse_volume(raw: Any) -> VolumeMount:
    if not isinstance(raw, dict):
        raise ValueError(f"volume must be a mapping, got {type(raw)}")
    return VolumeMount.model_validate(raw)


def load_manifest_from_path(path: Path) -> AgentManifest:
    if path.suffix.lower() == ".md":
        return _load_md_frontmatter(path)

    raw = path.read_text(encoding="utf-8")
    try:
        data: Any = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        raise ValueError(f"invalid YAML in {path}: {e}") from e
    if not isinstance(data, dict):
        raise ValueError(f"manifest root must be a mapping: {path}")
    try:
        return AgentManifest.model_validate(data)
    except ValidationError as e:
        raise ValueError(f"manifest validation failed for {path}:\n{e}") from e


def dump_manifest(manifest: AgentManifest) -> str:
    return yaml.safe_dump(
        manifest.model_dump(mode="json", by_alias=True),
        sort_keys=False,
        default_flow_style=False,
    )

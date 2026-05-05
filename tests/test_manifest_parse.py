from pathlib import Path

import pytest

from agentctl.manifest.io import load_manifest_from_path
from agentctl.manifest.v1 import API_VERSION_V1


def test_load_demo_manifest() -> None:
    p = Path(__file__).resolve().parent.parent / "examples" / "agents" / "demo.yaml"
    m = load_manifest_from_path(p)
    assert m.api_version == API_VERSION_V1
    assert m.metadata.name == "demo"
    assert m.spec.runtime == "pydantic-ai"


def test_mcp_server_validation() -> None:
    from agentctl.manifest.v1 import McpServer

    with pytest.raises(ValueError):
        McpServer(name="x", transport="stdio", command=None)


def test_mcp_bearer_serialization() -> None:
    from agentctl.manifest.v1 import McpServer

    m = McpServer(
        name="gitea",
        transport="http",
        url="http://gitea-mcp:8080/mcp",
        bearerFromEnv="GITEA_ACCESS_TOKEN",
    )
    d = m.model_dump(mode="python", by_alias=True)
    assert d["bearerFromEnv"] == "GITEA_ACCESS_TOKEN"


def test_volume_mutually_exclusive() -> None:
    from agentctl.manifest.v1 import AgentManifest, VolumeMount

    with pytest.raises(ValueError):
        VolumeMount(target="/a", name="v", hostPath="/b")

    with pytest.raises(ValueError):
        VolumeMount(target="/a")


def test_fs_tools_require_volumes(tmp_path) -> None:
    from agentctl.manifest.io import load_manifest_from_path

    bad = """
apiVersion: agentctl/v1
metadata:
  name: bad
spec:
  fsTools:
    enabled: true
  model:
    type: ollama
    model_id: m
  deploy:
    port: 8080
"""
    p = tmp_path / "bad.yaml"
    p.write_text(bad, encoding="utf-8")
    with pytest.raises(ValueError):
        load_manifest_from_path(p)


# ---------------------------------------------------------------------------
# Markdown frontmatter manifest tests
# ---------------------------------------------------------------------------


def test_load_md_manifest_basic(tmp_path: Path) -> None:
    """A .md file with frontmatter and body is parsed correctly."""
    md = tmp_path / "myagent.md"
    md.write_text(
        """---
name: myagent
description: "Test agent"
runtime: pydantic-ai
model:
  type: ollama
  model_id: llama3.2
  base_url: http://ollama:11434/v1
deploy:
  port: 8099
---
You are a helpful test agent.
""",
        encoding="utf-8",
    )
    m = load_manifest_from_path(md)
    assert m.api_version == API_VERSION_V1
    assert m.metadata.name == "myagent"
    assert m.metadata.description == "Test agent"
    assert m.spec.runtime == "pydantic-ai"
    assert m.spec.model.type == "ollama"
    assert m.spec.model.model_id == "llama3.2"  # type: ignore[union-attr]
    assert m.spec.prompts.get("system") == "You are a helpful test agent."
    assert m.spec.deploy.port == 8099


def test_load_md_manifest_with_volumes_and_tools(tmp_path: Path) -> None:
    """Volumes and tools frontmatter fields are mapped to spec correctly."""
    md = tmp_path / "devagent.md"
    md.write_text(
        """---
name: devagent
model:
  type: ollama
  model_id: llama3.2
volumes:
  - target: /workspace
    hostPath: .workspace
tools: [ls, grep, edit]
---
You are a developer.
""",
        encoding="utf-8",
    )
    m = load_manifest_from_path(md)
    assert len(m.spec.workspaces.volumes) == 1
    assert m.spec.workspaces.volumes[0].target == "/workspace"
    assert m.spec.workspaces.volumes[0].host_path == ".workspace"
    assert m.spec.fs_tools is not None
    assert m.spec.fs_tools.enabled is True
    assert set(m.spec.fs_tools.allow) == {"ls", "grep", "edit"}


def test_load_md_manifest_no_frontmatter_raises(tmp_path: Path) -> None:
    """A .md file without frontmatter should raise ValueError."""
    md = tmp_path / "bad.md"
    md.write_text("Just plain text, no frontmatter.", encoding="utf-8")
    with pytest.raises(ValueError, match="frontmatter"):
        load_manifest_from_path(md)


def test_load_md_manifest_agents_folder() -> None:
    """Load each agent definition from the .agents/ folder."""
    agents_dir = Path(__file__).resolve().parent.parent / ".agents"
    for agent_file in sorted(agents_dir.glob("*.md")):
        m = load_manifest_from_path(agent_file)
        assert m.metadata.name, f"{agent_file} must have a name"
        assert m.spec.model.type == "ollama", f"{agent_file} must use ollama model"
        assert "system" in m.spec.prompts, f"{agent_file} must have a system prompt"

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

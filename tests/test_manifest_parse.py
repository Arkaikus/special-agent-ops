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

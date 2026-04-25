from pathlib import Path

import pytest

from agentctl.cli.apply import run_apply
from agentctl.manifest.io import load_manifest_from_path


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    (tmp_path / "examples" / "agents").mkdir(parents=True)
    demo = Path(__file__).resolve().parent.parent / "examples" / "agents" / "demo.yaml"
    import shutil

    shutil.copy(demo, tmp_path / "examples" / "agents" / "demo.yaml")
    return tmp_path


def test_apply_generates_server(repo_root: Path) -> None:
    import os

    os.chdir(repo_root)
    man = repo_root / "examples" / "agents" / "demo.yaml"
    run_apply(man, dry_run=False, force=True)
    server = repo_root / ".agents" / "demo" / "python" / "server.py"
    text = server.read_text(encoding="utf-8")
    assert "FastAPI" in text
    assert "OllamaModel" in text
    assert "/invoke" in text


def test_openai_compatible_in_manifest(repo_root: Path) -> None:
    import os

    os.chdir(repo_root)
    p = repo_root / "examples" / "agents" / "codex.yaml"
    p.write_text(
        """
apiVersion: agentctl/v1
metadata:
  name: codex
spec:
  runtime: pydantic-ai
  model:
    type: openai_compatible
    model_id: gpt-4o-mini
    base_url: https://api.openai.com/v1
  prompts:
    system: test
  deploy:
    port: 8090
""",
        encoding="utf-8",
    )
    m = load_manifest_from_path(p)
    assert m.spec.model.type == "openai_compatible"
    run_apply(p, dry_run=False, force=True)
    t = (repo_root / ".agents" / "codex" / "python" / "server.py").read_text(encoding="utf-8")
    assert "OpenAIChatModel" in t

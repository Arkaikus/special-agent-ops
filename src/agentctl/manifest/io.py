from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from agentctl.manifest.v1 import AgentManifest


def load_manifest_from_path(path: Path) -> AgentManifest:
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

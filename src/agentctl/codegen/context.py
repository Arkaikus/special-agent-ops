from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentctl.manifest.v1 import AgentManifest


@dataclass
class CodegenContext:
    manifest: AgentManifest
    repo_root: Path
    output_root: Path  # .agents/{name}/

    @property
    def agent_name(self) -> str:
        return self.manifest.metadata.name

    @classmethod
    def from_manifest(cls, manifest: AgentManifest, repo_root: Path) -> CodegenContext:
        name = manifest.metadata.name
        output_root = repo_root / ".agents" / name
        return cls(manifest=manifest, repo_root=repo_root, output_root=output_root)

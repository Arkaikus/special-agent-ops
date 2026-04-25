from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

API_VERSION_V1 = "agentctl/v1"


class Metadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, pattern=r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")


class ModelAnthropic(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["anthropic"] = "anthropic"
    model_id: str
    api_key_env: str = "ANTHROPIC_API_KEY"
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


class ModelOllama(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["ollama"] = "ollama"
    model_id: str
    base_url: str = "http://host.docker.internal:11434/v1"
    api_key_env: str | None = None
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


class ModelOpenAICompatible(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["openai_compatible"] = "openai_compatible"
    model_id: str
    base_url: str
    api_key_env: str | None = "OPENAI_API_KEY"
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)


ModelConfig = Annotated[
    ModelAnthropic | ModelOllama | ModelOpenAICompatible,
    Field(discriminator="type"),
]


class McpServer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    transport: Literal["stdio", "sse", "http"] = "stdio"
    command: str | None = None
    args: list[str] = Field(default_factory=list)
    url: str | None = None
    env_from: list[str] = Field(default_factory=list, alias="envFrom")

    @model_validator(mode="after")
    def transport_requires_fields(self) -> McpServer:
        if self.transport == "stdio" and not self.command:
            raise ValueError("stdio MCP server requires command")
        if self.transport in ("sse", "http") and not self.url:
            raise ValueError(f"{self.transport} MCP server requires url")
        return self


class SkillRef(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    path: str | None = None
    git: str | None = None
    inline_prompt: str | None = Field(None, alias="inlinePrompt")

    @model_validator(mode="after")
    def one_source(self) -> SkillRef:
        n = sum(x is not None for x in (self.path, self.git, self.inline_prompt))
        if n != 1:
            raise ValueError("skill must set exactly one of path, git, inlinePrompt")
        return self


class DeployConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    image: str | None = None
    compose_service: str | None = Field(None, alias="composeService")
    port: int = Field(default=8080, ge=1, le=65535)
    build_context: str | None = Field(None, alias="buildContext")


class AgentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    runtime: Literal["pydantic-ai", "mcp-agent", "swarm-rs"] = "pydantic-ai"
    model: ModelConfig
    mcp_servers: list[McpServer] = Field(default_factory=list, alias="mcpServers")
    skills: list[SkillRef] = Field(default_factory=list)
    prompts: dict[str, str] = Field(default_factory=dict)
    deploy: DeployConfig = Field(default_factory=DeployConfig)


class AgentManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    api_version: str = Field(alias="apiVersion")
    metadata: Metadata
    spec: AgentSpec

    @model_validator(mode="after")
    def api_version_ok(self) -> AgentManifest:
        if self.api_version != API_VERSION_V1:
            raise ValueError(f"unsupported apiVersion {self.api_version!r}; expected {API_VERSION_V1!r}")
        return self

    def model_dump_yaml_safe(self) -> dict[str, Any]:
        return self.model_dump(mode="json", by_alias=True)

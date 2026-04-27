from __future__ import annotations

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str = ""
    default_agent: str | None = None
    default_agent_port: int = 8080


class ProjectRead(BaseModel):
    id: int
    name: str
    description: str
    default_agent: str | None
    default_agent_port: int


class ColumnCreate(BaseModel):
    title: str = Field(min_length=1)
    position: int = 0


class CardCreate(BaseModel):
    column_id: int
    title: str = Field(min_length=1)
    body: str = ""
    position: int = 0
    agent_name: str | None = None
    priority: int = Field(default=0, ge=0, le=3)
    team_label: str = ""


class CardMove(BaseModel):
    column_id: int
    position: int = 0


class CardUpdate(BaseModel):
    column_id: int | None = None
    title: str | None = Field(default=None, min_length=1)
    body: str | None = None
    position: int | None = None
    agent_name: str | None = None
    priority: int | None = Field(default=None, ge=0, le=3)
    team_label: str | None = None


class CardRead(BaseModel):
    id: int
    column_id: int
    title: str
    body: str
    position: int
    agent_name: str | None
    priority: int
    team_label: str


class ColumnRead(BaseModel):
    id: int
    title: str
    position: int
    cards: list[CardRead]


class BoardRead(BaseModel):
    project_id: int
    columns: list[ColumnRead]


class AgentRegister(BaseModel):
    name: str = Field(min_length=1)
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)


class AgentRead(BaseModel):
    id: int
    name: str
    host: str
    port: int
    project_ids: list[int]
    last_seen_at: str
    available: bool


class InvokeRequest(BaseModel):
    message: str = Field(min_length=1)
    project_id: int | None = None
    agent_name: str | None = None
    agent_port: int | None = None
    registered_agent_id: int | None = None
    agent_lookup: str | None = None


class InvokeResponse(BaseModel):
    output: str
    agent: str

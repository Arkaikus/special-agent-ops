from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str = ""
    default_agent: str | None = None
    default_agent_port: int = 8080


class BoardColumn(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    title: str
    position: int = 0


class Card(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    column_id: int = Field(foreign_key="boardcolumn.id")
    title: str
    body: str = ""
    position: int = 0
    agent_name: str | None = None
    priority: int = 0
    team_label: str = ""


class RegisteredAgent(SQLModel, table=True):
    __tablename__ = "registered_agent"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    host: str
    port: int
    last_seen_at: datetime = Field(default_factory=_utc_now)


class AgentProject(SQLModel, table=True):
    """Associates a registered agent with one or more projects (UI / organization)."""

    __tablename__ = "agent_project"
    __table_args__ = (UniqueConstraint("agent_id", "project_id", name="uq_agent_project"),)

    id: int | None = Field(default=None, primary_key=True)
    agent_id: int = Field(foreign_key="registered_agent.id", index=True)
    project_id: int = Field(foreign_key="project.id", index=True)

from __future__ import annotations

from sqlmodel import Field, SQLModel


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

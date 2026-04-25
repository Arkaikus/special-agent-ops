from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from agent_gateway.api.schemas import ProjectCreate, ProjectRead
from agent_gateway.db import get_session
from agent_gateway.models.orm import BoardColumn, Project

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _default_columns(session: Session, project_id: int) -> None:
    for i, title in enumerate(("Todo", "Doing", "Done")):
        session.add(BoardColumn(project_id=project_id, title=title, position=i))
    session.commit()


@router.post("", response_model=ProjectRead)
def create_project(body: ProjectCreate, session: Session = Depends(get_session)) -> Project:
    p = Project(
        name=body.name,
        description=body.description,
        default_agent=body.default_agent,
        default_agent_port=body.default_agent_port,
    )
    session.add(p)
    session.commit()
    session.refresh(p)
    _default_columns(session, p.id)  # type: ignore[arg-type]
    return p


@router.get("", response_model=list[ProjectRead])
def list_projects(session: Session = Depends(get_session)) -> list[Project]:
    return list(session.exec(select(Project)).all())


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, session: Session = Depends(get_session)) -> Project:
    p = session.get(Project, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="project not found")
    return p

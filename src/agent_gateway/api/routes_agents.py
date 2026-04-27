from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import exists, or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from agent_gateway.api.schemas import AgentRead, AgentRegister
from agent_gateway.db import get_session
from agent_gateway.models.orm import AgentProject, Project, RegisteredAgent

router = APIRouter(prefix="/api/agents", tags=["agents"])

AGENT_AVAILABLE_TTL_SECONDS = 90


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _project_ids_for_agent(session: Session, agent_id: int) -> list[int]:
    rows = session.exec(
        select(AgentProject.project_id).where(AgentProject.agent_id == agent_id)
    ).all()
    return sorted({int(r) for r in rows})


def _agent_to_read(session: Session, row: RegisteredAgent, *, now: datetime) -> AgentRead:
    seen = row.last_seen_at
    if seen.tzinfo is None:
        seen = seen.replace(tzinfo=timezone.utc)
    delta = now - seen
    available = delta.total_seconds() < AGENT_AVAILABLE_TTL_SECONDS
    return AgentRead(
        id=row.id,  # type: ignore[arg-type]
        name=row.name,
        host=row.host,
        port=row.port,
        project_ids=_project_ids_for_agent(session, row.id),  # type: ignore[arg-type]
        last_seen_at=seen.isoformat(),
        available=available,
    )


@router.post("/register", response_model=AgentRead)
def register_agent(body: AgentRegister, session: Session = Depends(get_session)) -> AgentRead:
    stmt = select(RegisteredAgent).where(RegisteredAgent.name == body.name)
    existing = session.exec(stmt).first()
    now = _utc_now()
    if existing:
        existing.host = body.host
        existing.port = body.port
        existing.last_seen_at = now
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return _agent_to_read(session, existing, now=now)

    row = RegisteredAgent(
        name=body.name,
        host=body.host,
        port=body.port,
        last_seen_at=now,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return _agent_to_read(session, row, now=now)


@router.get("", response_model=list[AgentRead])
def list_agents(
    for_project_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
) -> list[AgentRead]:
    stmt = select(RegisteredAgent).order_by(col(RegisteredAgent.name))
    if for_project_id is not None:
        if not session.get(Project, for_project_id):
            raise HTTPException(status_code=404, detail="project not found")
        has_any_link = exists(
            select(AgentProject.id).where(AgentProject.agent_id == RegisteredAgent.id)
        )
        linked_here = exists(
            select(AgentProject.id).where(
                AgentProject.agent_id == RegisteredAgent.id,
                AgentProject.project_id == for_project_id,
            )
        )
        stmt = stmt.where(or_(~has_any_link, linked_here))
    rows = list(session.exec(stmt).all())
    now = _utc_now()
    return [_agent_to_read(session, r, now=now) for r in rows]


@router.get("/{agent_id}", response_model=AgentRead)
def get_agent(agent_id: int, session: Session = Depends(get_session)) -> AgentRead:
    row = session.get(RegisteredAgent, agent_id)
    if not row:
        raise HTTPException(status_code=404, detail="agent not found")
    return _agent_to_read(session, row, now=_utc_now())


@router.post("/{agent_id}/projects/{project_id}", response_model=AgentRead)
def add_agent_project(
    agent_id: int, project_id: int, session: Session = Depends(get_session)
) -> AgentRead:
    if not session.get(RegisteredAgent, agent_id):
        raise HTTPException(status_code=404, detail="agent not found")
    if not session.get(Project, project_id):
        raise HTTPException(status_code=404, detail="project not found")
    link = AgentProject(agent_id=agent_id, project_id=project_id)
    session.add(link)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="agent already linked to project") from None
    row = session.get(RegisteredAgent, agent_id)
    assert row is not None
    return _agent_to_read(session, row, now=_utc_now())


@router.delete("/{agent_id}/projects/{project_id}", response_model=AgentRead)
def remove_agent_project(
    agent_id: int, project_id: int, session: Session = Depends(get_session)
) -> AgentRead:
    row = session.get(RegisteredAgent, agent_id)
    if not row:
        raise HTTPException(status_code=404, detail="agent not found")
    stmt = select(AgentProject).where(
        AgentProject.agent_id == agent_id,
        AgentProject.project_id == project_id,
    )
    link = session.exec(stmt).first()
    if not link:
        raise HTTPException(status_code=404, detail="link not found")
    session.delete(link)
    session.commit()
    session.refresh(row)
    return _agent_to_read(session, row, now=_utc_now())

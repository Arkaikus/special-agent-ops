from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from agent_gateway.api.schemas import InvokeRequest, InvokeResponse
from agent_gateway.db import get_session
from agent_gateway.models.orm import Project, RegisteredAgent
from agent_gateway.services.agent_runner import run_agent_http
from agent_gateway.services.bus import get_bus

router = APIRouter(prefix="/api", tags=["invoke"])


def _resolve_registered(
    session: Session,
    *,
    registered_agent_id: int | None,
    agent_lookup: str | None,
) -> RegisteredAgent | None:
    if registered_agent_id is not None:
        row = session.get(RegisteredAgent, registered_agent_id)
        if not row:
            raise HTTPException(status_code=404, detail="registered agent not found")
        return row
    if agent_lookup:
        stmt = select(RegisteredAgent).where(RegisteredAgent.name == agent_lookup)
        return session.exec(stmt).first()
    return None


@router.post("/invoke", response_model=InvokeResponse)
async def invoke(
    body: InvokeRequest,
    session: Session = Depends(get_session),
) -> InvokeResponse:
    reg = _resolve_registered(
        session,
        registered_agent_id=body.registered_agent_id,
        agent_lookup=body.agent_lookup,
    )

    agent_host: str | None = None
    port = body.agent_port or 8080

    if reg is not None:
        agent_host = reg.host
        port = reg.port
    else:
        agent_host = body.agent_name
        port = body.agent_port or 8080

        if body.project_id is not None:
            p = session.get(Project, body.project_id)
            if not p:
                raise HTTPException(status_code=404, detail="project not found")
            if agent_host is None and p.default_agent:
                agent_host = p.default_agent
            if body.agent_port is None and reg is None:
                port = p.default_agent_port

    if not agent_host:
        raise HTTPException(
            status_code=400,
            detail="registered_agent_id, agent_lookup, agent_name, or project default_agent required",
        )

    invoke_context: dict | None = None
    if body.project_id is not None:
        invoke_context = {"project_id": body.project_id}

    url = f"http://{agent_host}:{port}/invoke"
    out = await run_agent_http(url, body.message, context=invoke_context)
    bus = get_bus()
    if bus and body.project_id is not None:
        await bus.publish(
            str(body.project_id),
            "invoke",
            {"agent": agent_host, "message": body.message},
        )
    display_agent = reg.name if reg is not None else agent_host
    return InvokeResponse(output=out, agent=display_agent)

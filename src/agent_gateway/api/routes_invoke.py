from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from agent_gateway.api.schemas import InvokeRequest, InvokeResponse
from agent_gateway.db import get_session
from agent_gateway.models.orm import Project
from agent_gateway.services.agent_runner import run_agent_http
from agent_gateway.services.bus import get_bus

router = APIRouter(prefix="/api", tags=["invoke"])


@router.post("/invoke", response_model=InvokeResponse)
async def invoke(
    body: InvokeRequest,
    session: Session = Depends(get_session),
) -> InvokeResponse:
    agent_host: str | None = body.agent_name
    port = body.agent_port or 8080

    if body.project_id is not None:
        p = session.get(Project, body.project_id)
        if not p:
            raise HTTPException(status_code=404, detail="project not found")
        if agent_host is None and p.default_agent:
            agent_host = p.default_agent
        if body.agent_port is None:
            port = p.default_agent_port

    if not agent_host:
        raise HTTPException(
            status_code=400,
            detail="agent_name or project with default_agent required",
        )

    url = f"http://{agent_host}:{port}/invoke"
    out = await run_agent_http(url, body.message)
    bus = get_bus()
    if bus and body.project_id is not None:
        await bus.publish(str(body.project_id), "invoke", {"agent": agent_host, "message": body.message})
    return InvokeResponse(output=out, agent=agent_host)

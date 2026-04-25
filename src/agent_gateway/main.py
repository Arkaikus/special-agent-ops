from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_gateway.api.routes_board import router as board_router
from agent_gateway.api.routes_health import router as health_router
from agent_gateway.api.routes_invoke import router as invoke_router
from agent_gateway.api.routes_projects import router as projects_router
from agent_gateway.db import init_db
from agent_gateway.services.bus import set_bus
from agent_gateway.settings import settings
from agentctl.redis_bus.client import RedisBus


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("data", exist_ok=True)
    init_db()
    bus = RedisBus(settings.redis_url)
    await bus.connect()
    set_bus(bus)
    yield
    await bus.aclose()
    set_bus(None)


app = FastAPI(title="agent-gateway", lifespan=lifespan)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(projects_router)
app.include_router(board_router)
app.include_router(invoke_router)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "agent_gateway.main:app",
        host=os.environ.get("GATEWAY_HOST", "0.0.0.0"),
        port=int(os.environ.get("GATEWAY_PORT", "8000")),
        reload=False,
    )


if __name__ == "__main__":
    main()

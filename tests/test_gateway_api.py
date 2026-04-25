from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from agent_gateway.api.routes_board import router as board_router
from agent_gateway.api.routes_health import router as health_router
from agent_gateway.api.routes_projects import router as projects_router
from agent_gateway.db import get_session
from agent_gateway.models import orm as _orm  # noqa: F401

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app = FastAPI()
    app.include_router(health_router)
    app.include_router(projects_router)
    app.include_router(board_router)
    app.dependency_overrides[get_session] = override_session

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_project_and_board(client: TestClient) -> None:
    r = client.post(
        "/api/projects",
        json={
            "name": "P1",
            "description": "",
            "default_agent": None,
            "default_agent_port": 8080,
        },
    )
    assert r.status_code == 200
    pid = r.json()["id"]
    b = client.get(f"/api/projects/{pid}/board")
    assert b.status_code == 200
    cols = b.json()["columns"]
    assert len(cols) == 3

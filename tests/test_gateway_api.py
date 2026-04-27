from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from agent_gateway.api.routes_agents import AGENT_AVAILABLE_TTL_SECONDS, router as agents_router
from agent_gateway.api.routes_board import router as board_router
from agent_gateway.api.routes_health import router as health_router
from agent_gateway.api.routes_invoke import router as invoke_router
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
    app.include_router(agents_router)
    app.include_router(board_router)
    app.include_router(invoke_router)
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


def test_register_and_list_agents(client: TestClient) -> None:
    r = client.post(
        "/api/projects",
        json={
            "name": "P2",
            "description": "",
            "default_agent": None,
            "default_agent_port": 8080,
        },
    )
    pid = r.json()["id"]
    reg = client.post(
        "/api/agents/register",
        json={"name": "demo-agent", "host": "demo-agent", "port": 9000},
    )
    assert reg.status_code == 200
    body = reg.json()
    assert body["name"] == "demo-agent"
    assert body["project_ids"] == []
    assert body["available"] is True
    aid = body["id"]

    all_agents = client.get("/api/agents")
    assert all_agents.status_code == 200
    assert len(all_agents.json()) == 1
    assert all_agents.json()[0]["id"] == aid

    filtered = client.get(f"/api/agents?for_project_id={pid}")
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1

    one = client.get(f"/api/agents/{aid}")
    assert one.status_code == 200
    assert one.json()["host"] == "demo-agent"

    link_r = client.post(f"/api/agents/{aid}/projects/{pid}")
    assert link_r.status_code == 200
    assert link_r.json()["project_ids"] == [pid]

    dup = client.post(f"/api/agents/{aid}/projects/{pid}")
    assert dup.status_code == 409


def test_invoke_by_registered_agent_id(client: TestClient) -> None:
    r = client.post(
        "/api/projects",
        json={
            "name": "P3",
            "description": "",
            "default_agent": None,
            "default_agent_port": 8080,
        },
    )
    pid = r.json()["id"]
    reg = client.post(
        "/api/agents/register",
        json={"name": "svc", "host": "mock-host", "port": 9999},
    )
    aid = reg.json()["id"]

    with patch(
        "agent_gateway.api.routes_invoke.run_agent_http",
        new_callable=AsyncMock,
        return_value="mocked-output",
    ) as m:
        inv = client.post(
            "/api/invoke",
            json={
                "message": "hi",
                "project_id": pid,
                "registered_agent_id": aid,
            },
        )
    assert inv.status_code == 200
    assert inv.json()["output"] == "mocked-output"
    assert inv.json()["agent"] == "svc"
    m.assert_awaited_once()
    call_url = m.await_args[0][0]
    assert call_url == "http://mock-host:9999/invoke"
    assert m.await_args.kwargs.get("context") == {"project_id": pid}


def test_invoke_agent_lookup_no_project(client: TestClient) -> None:
    client.post(
        "/api/agents/register",
        json={"name": "lookup-me", "host": "h2", "port": 7777},
    )
    with patch(
        "agent_gateway.api.routes_invoke.run_agent_http",
        new_callable=AsyncMock,
        return_value="ok",
    ) as m:
        inv = client.post(
            "/api/invoke",
            json={"message": "m", "agent_lookup": "lookup-me"},
        )
    assert inv.status_code == 200
    m.assert_awaited_once()
    assert m.await_args[0][0] == "http://h2:7777/invoke"
    assert m.await_args.kwargs.get("context") is None


def test_agent_project_link_and_unlink(client: TestClient) -> None:
    p1 = client.post(
        "/api/projects",
        json={
            "name": "A",
            "description": "",
            "default_agent": None,
            "default_agent_port": 8080,
        },
    ).json()["id"]
    p2 = client.post(
        "/api/projects",
        json={
            "name": "B",
            "description": "",
            "default_agent": None,
            "default_agent_port": 8080,
        },
    ).json()["id"]
    aid = client.post(
        "/api/agents/register",
        json={"name": "multi", "host": "h", "port": 1},
    ).json()["id"]
    client.post(f"/api/agents/{aid}/projects/{p1}")
    client.post(f"/api/agents/{aid}/projects/{p2}")
    body = client.get(f"/api/agents/{aid}").json()
    assert set(body["project_ids"]) == {p1, p2}
    client.delete(f"/api/agents/{aid}/projects/{p1}")
    body2 = client.get(f"/api/agents/{aid}").json()
    assert body2["project_ids"] == [p2]


def test_card_patch_and_delete(client: TestClient) -> None:
    r = client.post(
        "/api/projects",
        json={
            "name": "P4",
            "description": "",
            "default_agent": None,
            "default_agent_port": 8080,
        },
    )
    pid = r.json()["id"]
    board = client.get(f"/api/projects/{pid}/board").json()
    col_id = board["columns"][0]["id"]
    cr = client.post(
        f"/api/projects/{pid}/cards",
        json={"column_id": col_id, "title": "T1", "body": "b", "position": 0},
    )
    assert cr.status_code == 200
    cid = cr.json()["id"]

    up = client.patch(
        f"/api/cards/{cid}",
        json={"title": "T2", "priority": 2, "team_label": "Alpha"},
    )
    assert up.status_code == 200
    assert up.json()["title"] == "T2"
    assert up.json()["priority"] == 2
    assert up.json()["team_label"] == "Alpha"

    dl = client.delete(f"/api/cards/{cid}")
    assert dl.status_code == 200


def test_agent_available_ttl(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from datetime import datetime, timedelta, timezone

    from agent_gateway.api import routes_agents as ra

    client.post(
        "/api/projects",
        json={
            "name": "P5",
            "description": "",
            "default_agent": None,
            "default_agent_port": 8080,
        },
    )
    reg = client.post(
        "/api/agents/register",
        json={"name": "stale", "host": "h", "port": 1},
    )
    aid = reg.json()["id"]

    base = datetime.now(timezone.utc)
    monkeypatch.setattr(
        ra,
        "_utc_now",
        lambda: base + timedelta(seconds=AGENT_AVAILABLE_TTL_SECONDS + 30),
    )
    listed2 = client.get(f"/api/agents/{aid}")
    assert listed2.json()["available"] is False

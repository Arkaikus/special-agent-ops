from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from agent_gateway.settings import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)


def _sqlite_add_column_if_missing(table: str, column: str, ddl: str) -> None:
    insp = inspect(engine)
    if not insp.has_table(table):
        return
    cols = {c["name"] for c in insp.get_columns(table)}
    if column in cols:
        return
    with engine.connect() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))
        conn.commit()


def init_db() -> None:
    # Imported here to register tables
    from agent_gateway import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    if settings.database_url.startswith("sqlite"):
        _sqlite_add_column_if_missing("card", "priority", "priority INTEGER NOT NULL DEFAULT 0")
        _sqlite_add_column_if_missing("card", "team_label", "team_label VARCHAR NOT NULL DEFAULT ''")
        _sqlite_migrate_registered_agent_to_agent_project()


def _sqlite_migrate_registered_agent_to_agent_project() -> None:
    """Move legacy single-project FK on registered_agent into agent_project junction rows."""
    insp = inspect(engine)
    if not insp.has_table("registered_agent") or not insp.has_table("agent_project"):
        return
    with engine.connect() as conn:
        cols = {c["name"] for c in insp.get_columns("registered_agent")}
        if "visual_project_id" in cols:
            conn.execute(
                text(
                    "INSERT OR IGNORE INTO agent_project (agent_id, project_id) "
                    "SELECT id, visual_project_id FROM registered_agent "
                    "WHERE visual_project_id IS NOT NULL"
                )
            )
            try:
                conn.execute(text("ALTER TABLE registered_agent DROP COLUMN visual_project_id"))
            except Exception:
                pass
            conn.commit()
            cols = {c["name"] for c in inspect(engine).get_columns("registered_agent")}
        if "project_id" in cols:
            conn.execute(
                text(
                    "INSERT OR IGNORE INTO agent_project (agent_id, project_id) "
                    "SELECT id, project_id FROM registered_agent WHERE project_id IS NOT NULL"
                )
            )
            try:
                conn.execute(text("ALTER TABLE registered_agent DROP COLUMN project_id"))
            except Exception:
                pass
            conn.commit()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

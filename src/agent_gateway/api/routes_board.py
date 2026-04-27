from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, col, select

from agent_gateway.api.schemas import BoardRead, CardCreate, CardRead, CardUpdate, ColumnCreate, ColumnRead
from agent_gateway.db import get_session
from agent_gateway.models.orm import BoardColumn, Card, Project

router = APIRouter(prefix="/api", tags=["board"])


def _card_read(card: Card) -> CardRead:
    return CardRead(
        id=card.id,  # type: ignore[arg-type]
        column_id=card.column_id,
        title=card.title,
        body=card.body,
        position=card.position,
        agent_name=card.agent_name,
        priority=card.priority,
        team_label=card.team_label,
    )


def _card_project_id(session: Session, card: Card) -> int:
    col = session.get(BoardColumn, card.column_id)
    if not col:
        raise HTTPException(status_code=400, detail="card column missing")
    return col.project_id


@router.get("/projects/{project_id}/board", response_model=BoardRead)
def get_board(project_id: int, session: Session = Depends(get_session)) -> BoardRead:
    if not session.get(Project, project_id):
        raise HTTPException(status_code=404, detail="project not found")
    cols = list(
        session.exec(
            select(BoardColumn)
            .where(BoardColumn.project_id == project_id)
            .order_by(col(BoardColumn.position))
        ).all()
    )
    out_cols: list[ColumnRead] = []
    for c in cols:
        cards = list(
            session.exec(
                select(Card).where(Card.column_id == c.id).order_by(col(Card.position))
            ).all()
        )
        out_cols.append(
            ColumnRead(
                id=c.id,  # type: ignore[arg-type]
                title=c.title,
                position=c.position,
                cards=[_card_read(card) for card in cards],
            )
        )
    return BoardRead(project_id=project_id, columns=out_cols)


@router.post("/projects/{project_id}/columns", response_model=ColumnRead)
def add_column(
    project_id: int, body: ColumnCreate, session: Session = Depends(get_session)
) -> ColumnRead:
    if not session.get(Project, project_id):
        raise HTTPException(status_code=404, detail="project not found")
    col = BoardColumn(project_id=project_id, title=body.title, position=body.position)
    session.add(col)
    session.commit()
    session.refresh(col)
    return ColumnRead(id=col.id, title=col.title, position=col.position, cards=[])  # type: ignore[arg-type]


@router.post("/projects/{project_id}/cards", response_model=CardRead)
def add_card(
    project_id: int, body: CardCreate, session: Session = Depends(get_session)
) -> CardRead:
    col = session.get(BoardColumn, body.column_id)
    if not col or col.project_id != project_id:
        raise HTTPException(status_code=400, detail="invalid column for project")
    card = Card(
        column_id=body.column_id,
        title=body.title,
        body=body.body,
        position=body.position,
        agent_name=body.agent_name,
        priority=body.priority,
        team_label=body.team_label,
    )
    session.add(card)
    session.commit()
    session.refresh(card)
    return _card_read(card)


@router.patch("/cards/{card_id}", response_model=CardRead)
def update_card(card_id: int, body: CardUpdate, session: Session = Depends(get_session)) -> CardRead:
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="card not found")
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="no fields to update")

    project_id = _card_project_id(session, card)

    if "column_id" in data:
        new_col = session.get(BoardColumn, data["column_id"])
        if not new_col or new_col.project_id != project_id:
            raise HTTPException(status_code=400, detail="invalid column for project")
        card.column_id = data["column_id"]
    if "title" in data:
        card.title = data["title"]
    if "body" in data:
        card.body = data["body"]
    if "position" in data:
        card.position = data["position"]
    if "agent_name" in data:
        card.agent_name = data["agent_name"]
    if "priority" in data:
        card.priority = data["priority"]
    if "team_label" in data:
        card.team_label = data["team_label"]

    session.add(card)
    session.commit()
    session.refresh(card)
    return _card_read(card)


@router.delete("/cards/{card_id}")
def delete_card(card_id: int, session: Session = Depends(get_session)) -> dict[str, str]:
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="card not found")
    session.delete(card)
    session.commit()
    return {"status": "ok"}

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, col, select

from agent_gateway.api.schemas import BoardRead, CardCreate, CardMove, CardRead, ColumnCreate, ColumnRead
from agent_gateway.db import get_session
from agent_gateway.models.orm import BoardColumn, Card, Project

router = APIRouter(prefix="/api", tags=["board"])


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
                cards=[
                    CardRead(
                        id=card.id,  # type: ignore[arg-type]
                        column_id=card.column_id,
                        title=card.title,
                        body=card.body,
                        position=card.position,
                        agent_name=card.agent_name,
                    )
                    for card in cards
                ],
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
    )
    session.add(card)
    session.commit()
    session.refresh(card)
    return CardRead(
        id=card.id,  # type: ignore[arg-type]
        column_id=card.column_id,
        title=card.title,
        body=card.body,
        position=card.position,
        agent_name=card.agent_name,
    )


@router.patch("/cards/{card_id}", response_model=CardRead)
def move_card(card_id: int, body: CardMove, session: Session = Depends(get_session)) -> CardRead:
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="card not found")
    col = session.get(BoardColumn, body.column_id)
    if not col:
        raise HTTPException(status_code=400, detail="invalid column")
    card.column_id = body.column_id
    card.position = body.position
    session.add(card)
    session.commit()
    session.refresh(card)
    return CardRead(
        id=card.id,  # type: ignore[arg-type]
        column_id=card.column_id,
        title=card.title,
        body=card.body,
        position=card.position,
        agent_name=card.agent_name,
    )

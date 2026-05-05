from __future__ import annotations

from fastapi import APIRouter

from agent_gateway.services.workspace_search import get_workspace_search

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


@router.post("/reindex")
def reindex_workspace() -> dict:
    """Re-scan the workspace folder and upsert all readable files into ChromaDB.

    Returns the number of files indexed. Safe to call multiple times; existing
    documents are updated (upserted) rather than duplicated.
    """
    ws = get_workspace_search()
    if ws is None:
        return {"indexed": 0, "detail": "workspace search not available"}
    indexed = ws.index_workspace()
    return {"indexed": indexed}


@router.get("/status")
def workspace_status() -> dict:
    """Return whether the workspace search service is available."""
    ws = get_workspace_search()
    return {"available": ws is not None}

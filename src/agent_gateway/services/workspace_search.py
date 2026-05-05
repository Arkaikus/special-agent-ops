from __future__ import annotations

"""Workspace similarity search backed by ChromaDB.

Files under the configured workspace path are embedded and stored in a ChromaDB
collection. On each agent invocation the middleware queries the collection with
the incoming message and injects the top-K relevant snippets as additional
context so the agent always has project-aware background.

ChromaDB is accessed via its HTTP client (``chromadb.HttpClient``), which
means the ChromaDB server runs as a separate container in the compose stack.
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Sequence

logger = logging.getLogger(__name__)

# Maximum characters read from a single workspace file.
_MAX_FILE_CHARS = 8_000
# Number of most-relevant snippets to inject per query.
_TOP_K = 3
# Collection name inside ChromaDB.
_COLLECTION = "workspace"

# Text extensions considered "readable" for embedding.
_TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".rst",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".py",
    ".ts",
    ".js",
    ".go",
    ".java",
    ".sh",
    ".env.example",
    ".cfg",
    ".ini",
    ".xml",
    ".html",
    ".css",
}


def _file_id(path: Path, workspace_root: Path) -> str:
    """Stable document ID: relative path from workspace root."""
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def _read_file(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return text[:_MAX_FILE_CHARS]
    except OSError:
        return None


class WorkspaceSearchService:
    """Index workspace files into ChromaDB and query them by similarity."""

    def __init__(self, chromadb_url: str, workspace_path: str) -> None:
        self._chromadb_url = chromadb_url
        self._workspace_path = Path(workspace_path)
        self._client = None
        self._collection = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Connect to ChromaDB and get/create the workspace collection."""
        try:
            import chromadb  # type: ignore[import-untyped]

            host, port = _parse_url(self._chromadb_url)
            self._client = chromadb.HttpClient(host=host, port=port)
            self._collection = self._client.get_or_create_collection(
                name=_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("WorkspaceSearchService connected to ChromaDB at %s", self._chromadb_url)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "WorkspaceSearchService: could not connect to ChromaDB (%s). "
                "Workspace context injection will be disabled.",
                exc,
            )
            self._client = None
            self._collection = None

    def close(self) -> None:
        self._client = None
        self._collection = None

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index_workspace(self) -> int:
        """Walk workspace_path and upsert all readable text files.

        Returns the number of files indexed.
        """
        if self._collection is None:
            return 0
        if not self._workspace_path.is_dir():
            logger.debug("Workspace path does not exist yet: %s", self._workspace_path)
            return 0

        indexed = 0
        for path in self._workspace_path.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in _TEXT_EXTENSIONS and "." not in path.name:
                continue
            content = _read_file(path)
            if content is None:
                continue
            doc_id = _file_id(path, self._workspace_path)
            try:
                self._collection.upsert(
                    ids=[doc_id],
                    documents=[content],
                    metadatas=[{"source": doc_id}],
                )
                indexed += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to upsert workspace file %s: %s", doc_id, exc)

        logger.info("WorkspaceSearchService indexed %d files from %s", indexed, self._workspace_path)
        return indexed

    # ------------------------------------------------------------------
    # Querying
    # ------------------------------------------------------------------

    def search(self, query: str, n_results: int = _TOP_K) -> list[str]:
        """Return the top-n most relevant workspace snippets for *query*.

        Returns an empty list when ChromaDB is unavailable or the workspace
        is empty.
        """
        if self._collection is None:
            return []
        try:
            count = self._collection.count()
            if count == 0:
                return []
            actual_n = min(n_results, count)
            results = self._collection.query(
                query_texts=[query],
                n_results=actual_n,
                include=["documents", "metadatas"],
            )
            docs: list[str] = []
            for doc, meta in zip(
                results.get("documents", [[]])[0],
                results.get("metadatas", [[]])[0],
            ):
                source = (meta or {}).get("source", "?")
                docs.append(f"[{source}]\n{doc}")
            return docs
        except Exception as exc:  # noqa: BLE001
            logger.warning("WorkspaceSearchService query failed: %s", exc)
            return []

    def build_context_prefix(self, query: str) -> str:
        """Return a formatted context block to prepend to the agent message."""
        snippets = self.search(query)
        if not snippets:
            return ""
        parts = ["<workspace_context>"]
        for snippet in snippets:
            parts.append(snippet)
        parts.append("</workspace_context>")
        return "\n\n".join(parts) + "\n\n"


# ---------------------------------------------------------------------------
# Module-level singleton (managed by gateway lifespan)
# ---------------------------------------------------------------------------

_service: WorkspaceSearchService | None = None


def get_workspace_search() -> WorkspaceSearchService | None:
    return _service


def set_workspace_search(svc: WorkspaceSearchService | None) -> None:
    global _service
    _service = svc


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_url(url: str) -> tuple[str, int]:
    """Extract (host, port) from an http(s)://host:port URL."""
    url = url.rstrip("/")
    if "://" in url:
        url = url.split("://", 1)[1]
    if ":" in url:
        host, port_str = url.rsplit(":", 1)
        return host, int(port_str)
    return url, 8000

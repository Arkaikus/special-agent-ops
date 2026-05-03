from __future__ import annotations

import logging
from collections.abc import AsyncIterator

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)


async def run_agent_http(
    url: str,
    message: str,
    *,
    context: dict | None = None,
    timeout: float = 120.0,
) -> str:
    """POST a message to an agent's /invoke endpoint and return its text output.

    Raises HTTPException(502) when the downstream agent is unreachable or
    returns a non-2xx status so callers get a structured JSON error instead of
    an unhandled Python traceback.
    """
    payload: dict = {"message": message}
    if context:
        payload["context"] = context
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
    except httpx.TimeoutException as exc:
        logger.warning("Agent timeout calling %s: %s", url, exc)
        raise HTTPException(
            status_code=504,
            detail=f"Agent timed out after {timeout}s",
        ) from exc
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Agent returned %s from %s: %s",
            exc.response.status_code,
            url,
            exc.response.text[:200],
        )
        raise HTTPException(
            status_code=502,
            detail=f"Agent returned HTTP {exc.response.status_code}",
        ) from exc
    except httpx.RequestError as exc:
        logger.warning("Agent unreachable at %s: %s", url, exc)
        raise HTTPException(
            status_code=502,
            detail=f"Agent unreachable: {exc}",
        ) from exc

    data = r.json()
    if isinstance(data, dict) and "output" in data:
        out = data["output"]
        return out if isinstance(out, str) else str(out)
    return str(data)


async def stream_agent_http(
    url: str,
    message: str,
    *,
    context: dict | None = None,
    timeout: float = 120.0,
) -> AsyncIterator[str]:
    """Stream text chunks from an agent's /invoke/stream SSE endpoint.

    Yields each non-empty data payload as a plain string.  Stops when the
    agent closes the connection or sends a ``[DONE]`` sentinel.

    Raises HTTPException(502/504) on network or upstream errors so callers
    can fall back to the buffered invoke path.
    """
    payload: dict = {"message": message}
    if context:
        payload["context"] = context
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, json=payload) as r:
                if r.status_code == 404:
                    # Agent does not support streaming
                    raise HTTPException(
                        status_code=404,
                        detail="Agent streaming endpoint not found",
                    )
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    chunk = line[len("data:"):].strip()
                    if not chunk or chunk == "[DONE]":
                        break
                    yield chunk
    except HTTPException:
        raise
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail=f"Agent stream timed out after {timeout}s",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Agent stream returned HTTP {exc.response.status_code}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Agent stream unreachable: {exc}",
        ) from exc

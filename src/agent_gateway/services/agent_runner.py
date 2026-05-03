from __future__ import annotations

import logging

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

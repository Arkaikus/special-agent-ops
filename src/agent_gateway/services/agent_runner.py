from __future__ import annotations

import httpx


async def run_agent_http(
    url: str,
    message: str,
    *,
    context: dict | None = None,
    timeout: float = 120.0,
) -> str:
    payload: dict = {"message": message}
    if context:
        payload["context"] = context
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "output" in data:
            out = data["output"]
            return out if isinstance(out, str) else str(out)
        return str(data)

from __future__ import annotations

import httpx


async def run_agent_http(url: str, message: str, timeout: float = 120.0) -> str:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(url, json={"message": message})
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict) and "output" in data:
            out = data["output"]
            return out if isinstance(out, str) else str(out)
        return str(data)

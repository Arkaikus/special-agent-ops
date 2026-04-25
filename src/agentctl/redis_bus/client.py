from __future__ import annotations

import json
from typing import Any

import redis.asyncio as redis


class RedisBus:
    """Thin async wrapper: pub/sub and optional streams."""

    def __init__(self, url: str) -> None:
        self.url = url
        self._client: redis.Redis | None = None

    async def connect(self) -> None:
        self._client = redis.from_url(self.url, decode_responses=True)

    async def aclose(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def channel(self, project: str, topic: str) -> str:
        return f"agentctl:{project}:{topic}"

    async def publish(self, project: str, topic: str, payload: dict[str, Any]) -> int:
        assert self._client is not None
        return await self._client.publish(self.channel(project, topic), json.dumps(payload))

    async def xadd(self, stream: str, fields: dict[str, str]) -> str:
        assert self._client is not None
        return await self._client.xadd(stream, fields)

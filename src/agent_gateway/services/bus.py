from __future__ import annotations

from agentctl.redis_bus.client import RedisBus

_bus: RedisBus | None = None


def set_bus(bus: RedisBus | None) -> None:
    global _bus
    _bus = bus


def get_bus() -> RedisBus | None:
    return _bus

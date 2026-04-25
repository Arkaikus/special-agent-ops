import pytest

pytest.importorskip("testcontainers")


from testcontainers.redis import RedisContainer  # noqa: E402

from agentctl.redis_bus.client import RedisBus  # noqa: E402


@pytest.mark.asyncio
async def test_redis_publish() -> None:
    with RedisContainer("redis:7-alpine") as redis:
        host = redis.get_container_host_ip()
        port = redis.get_exposed_port(6379)
        url = f"redis://{host}:{port}/0"
        bus = RedisBus(url)
        await bus.connect()
        try:
            n = await bus.publish("proj1", "events", {"x": 1})
            assert n >= 0
        finally:
            await bus.aclose()

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import PostgresRawSettings, RedisSettings, Settings
from app.infra.storage import base
from app.infra.storage.base import (
    REDIS,
    StorageHandle,
    StorageManager,
    StorageNotConfiguredError,
    StorageUnavailableError,
)
from app.main import create_app
from tests.fakes import make_handle

REDIS_SETTINGS = RedisSettings(dsn=SecretStr("redis://localhost"))
RAW_SETTINGS = PostgresRawSettings(dsn=SecretStr("postgresql://localhost"))


async def test_manager_opens_probes_and_closes(fake_backends: AsyncMock) -> None:
    client = object()
    check = AsyncMock()
    close = AsyncMock()
    fake_backends.return_value = make_handle(client, check, close)
    manager = StorageManager()

    await manager.open(Settings(redis=REDIS_SETTINGS))

    fake_backends.assert_awaited_once_with(REDIS_SETTINGS)
    assert await manager.get(REDIS) is client
    assert await manager.readiness() == {"redis": "ok"}
    check.side_effect = ConnectionError("down")
    assert await manager.readiness() == {"redis": "unavailable"}
    await manager.close()
    close.assert_awaited_once()
    assert manager.handles == {}


async def test_get_reports_missing_and_unreachable_backends() -> None:
    manager = StorageManager()
    with pytest.raises(StorageNotConfiguredError, match="redis is not configured"):
        await manager.get(REDIS)

    failing = AsyncMock(side_effect=ConnectionError("down"))
    manager.handles["redis"] = StorageHandle(acquire=failing, check=AsyncMock(), close=AsyncMock())
    with pytest.raises(StorageUnavailableError, match="redis is unavailable"):
        await manager.get(REDIS)


async def test_readiness_is_cached_and_bounded() -> None:
    check = AsyncMock()
    manager = StorageManager(readiness_cache_ttl=60)
    manager.handles["redis"] = make_handle(object(), check)
    assert await manager.readiness() == {"redis": "ok"}
    assert await manager.readiness() == {"redis": "ok"}
    check.assert_awaited_once()

    async def hang() -> None:
        await asyncio.sleep(10)

    slow = StorageManager(readiness_timeout=0.01)
    slow.handles["redis"] = make_handle(object(), hang)
    assert await slow.readiness() == {"redis": "unavailable"}


def test_ready_is_503_for_unavailable_backend(fake_backends: AsyncMock) -> None:
    check = AsyncMock(side_effect=ConnectionError("down"))
    fake_backends.return_value = make_handle(object(), check)
    settings = Settings(environment="test", readiness_cache_ttl=0, redis=REDIS_SETTINGS)
    with TestClient(create_app(settings), base_url="http://localhost") as client:
        assert client.get("/live").status_code == 200
        response = client.get("/ready")
        assert response.status_code == 503
        assert response.json()["dependencies"] == {"redis": "unavailable"}
        assert 'app_storage_available{backend="redis"} 0.0' in client.get("/metrics").text
        check.side_effect = None
        assert 'app_storage_available{backend="redis"} 1.0' in client.get("/metrics").text


async def test_missing_extra_has_actionable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(_: str) -> None:
        raise ModuleNotFoundError("No module named 'redis'", name="redis")

    monkeypatch.setattr(base, "import_module", missing)
    with pytest.raises(RuntimeError, match="Install the 'redis' extra"):
        await StorageManager().open(Settings(redis=REDIS_SETTINGS))


async def test_missing_driver_during_client_creation_has_actionable_error(
    fake_backends: AsyncMock,
) -> None:
    fake_backends.side_effect = ModuleNotFoundError("No module named 'psycopg'", name="psycopg")
    with pytest.raises(RuntimeError, match="Install the 'postgres-raw' extra"):
        await StorageManager().open(Settings(postgres_raw=RAW_SETTINGS))


async def test_adapter_import_error_is_not_reported_as_missing_extra(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken(_: str) -> None:
        raise ModuleNotFoundError("No module named 'internal'", name="internal")

    monkeypatch.setattr(base, "import_module", broken)
    with pytest.raises(ModuleNotFoundError, match="internal"):
        await StorageManager().open(Settings(redis=REDIS_SETTINGS))


async def test_partial_startup_closes_created_clients(fake_backends: AsyncMock) -> None:
    close = AsyncMock(side_effect=RuntimeError("close failed"))
    fake_backends.side_effect = [make_handle(object(), close=close), RuntimeError("create failed")]
    manager = StorageManager()

    with pytest.raises(RuntimeError, match="create failed"):
        await manager.open(Settings(postgres_raw=RAW_SETTINGS, redis=REDIS_SETTINGS))

    close.assert_awaited_once()
    assert manager.handles == {}


async def test_close_releases_every_client_after_one_close_fails(
    fake_backends: AsyncMock,
) -> None:
    closed: list[str] = []

    async def close_raw() -> None:
        closed.append("postgres_raw")

    async def close_redis() -> None:
        closed.append("redis")
        raise RuntimeError("close failed")

    fake_backends.side_effect = [
        make_handle(object(), close=close_raw),
        make_handle(object(), close=close_redis),
    ]
    manager = StorageManager()
    await manager.open(Settings(postgres_raw=RAW_SETTINGS, redis=REDIS_SETTINGS))

    await manager.close()

    assert closed == ["redis", "postgres_raw"]
    assert manager.handles == {}

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.api.dependencies.storage import (
    get_clickhouse,
    get_mongodb,
    get_postgres_raw,
    get_postgres_session,
    get_redis,
)
from app.api.v1.auth import get_current_principal
from app.infra.storage.base import StorageHandle, StorageManager
from tests.fakes import make_handle


async def test_unconfigured_storage_returns_503() -> None:
    with pytest.raises(HTTPException) as error:
        await get_redis(StorageManager())
    assert error.value.status_code == 503
    assert error.value.detail == "redis is not configured"


async def test_storage_dependencies_return_clients() -> None:
    manager = StorageManager()
    raw_pool, mongo_client, redis_client, clickhouse_client = object(), object(), object(), object()
    manager.handles = {
        "postgres_raw": make_handle(raw_pool),
        "mongodb": make_handle(mongo_client),
        "redis": make_handle(redis_client),
        "clickhouse": make_handle(clickhouse_client),
    }
    assert await get_postgres_raw(manager) is raw_pool
    assert await get_mongodb(manager) is mongo_client
    assert await get_redis(manager) is redis_client
    assert await get_clickhouse(manager) is clickhouse_client
    assert get_redis.__name__ == "get_redis"


async def test_unreachable_backend_returns_503() -> None:
    manager = StorageManager()
    manager.handles["clickhouse"] = StorageHandle(
        acquire=AsyncMock(side_effect=ConnectionError("down")),
        check=AsyncMock(),
        close=AsyncMock(),
    )
    with pytest.raises(HTTPException) as error:
        await get_clickhouse(manager)
    assert error.value.status_code == 503


async def test_orm_session_dependency() -> None:
    manager = StorageManager()
    session = object()
    factory = MagicMock()
    factory.return_value.__aenter__.return_value = session
    manager.handles["postgres_orm"] = make_handle(factory)
    dependency = get_postgres_session(manager)
    assert await anext(dependency) is session
    with pytest.raises(StopAsyncIteration):
        await anext(dependency)


async def test_auth_extension_is_closed_by_default() -> None:
    with pytest.raises(HTTPException) as error:
        await get_current_principal()
    assert error.value.status_code == 401

from collections.abc import AsyncIterator, Awaitable, Callable
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException

from app.api.dependencies.container import get_container
from app.container import AppContainer
from app.infra.storage.base import (
    CLICKHOUSE,
    MONGODB,
    POSTGRES_ORM,
    POSTGRES_RAW,
    REDIS,
    BackendSpec,
    StorageManager,
    StorageNotConfiguredError,
    StorageUnavailableError,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


def get_storage(container: Annotated[AppContainer, Depends(get_container)]) -> StorageManager:
    """Return storage bound during the application lifespan."""
    return container.storage


Storage = Annotated[StorageManager, Depends(get_storage)]


async def acquire[T](storage: StorageManager, spec: BackendSpec[T]) -> T:
    """Return a backend client, or raise 503 if it is not configured or not reachable."""
    try:
        return await storage.get(spec)
    except (StorageNotConfiguredError, StorageUnavailableError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def require[T](spec: BackendSpec[T]) -> Callable[[StorageManager], Awaitable[T]]:
    """Build a FastAPI dependency that returns the client for `spec`."""

    async def dependency(storage: Storage) -> T:
        return await acquire(storage, spec)

    dependency.__name__ = f"get_{spec.name}"
    return dependency


get_postgres_raw = require(POSTGRES_RAW)
get_clickhouse = require(CLICKHOUSE)
get_mongodb = require(MONGODB)
get_redis = require(REDIS)


async def get_postgres_session(storage: Storage) -> AsyncIterator[AsyncSession]:
    """Yield a per-request SQLAlchemy session; callers own the transaction."""
    factory = await acquire(storage, POSTGRES_ORM)
    async with factory() as session:
        yield session

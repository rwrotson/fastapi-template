from unittest.mock import AsyncMock, MagicMock, create_autospec
from uuid import uuid4

import pytest
from prometheus_client import REGISTRY
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction

from app.infra.storage.notes import NoteRow, PostgresNoteUnitOfWork
from app.services.notes import Note


def make_session() -> tuple[MagicMock, MagicMock]:
    """Create a mocked session with an active transaction."""
    transaction = create_autospec(AsyncSessionTransaction, instance=True)
    transaction.is_active = True

    async def commit() -> None:
        transaction.is_active = False

    transaction.commit.side_effect = commit
    session = create_autospec(AsyncSession, instance=True)
    session.begin = AsyncMock(return_value=transaction)
    return session, transaction


def metric_sample(name: str, labels: dict[str, str]) -> float:
    """Read a metric sample, treating an absent series as zero."""
    return REGISTRY.get_sample_value(name, labels) or 0


async def test_commit_records_database_metrics() -> None:
    session, transaction = make_session()
    session.get.return_value = NoteRow(id=uuid4(), content="saved")
    labels = {"backend": "postgres_orm", "operation": "notes.insert", "result": "ok"}
    before = metric_sample("app_database_operations_total", labels)

    async with PostgresNoteUnitOfWork(session) as unit_of_work:
        await unit_of_work.notes.add(Note(id=uuid4(), content="example"))
        assert await unit_of_work.notes.get(uuid4()) is not None
        await unit_of_work.commit()

    transaction.commit.assert_awaited_once_with()
    transaction.rollback.assert_not_awaited()
    assert metric_sample("app_database_operations_total", labels) == before + 1


async def test_failed_flush_rolls_back() -> None:
    session, transaction = make_session()
    session.flush.side_effect = RuntimeError("insert failed")

    with pytest.raises(RuntimeError, match="insert failed"):
        async with PostgresNoteUnitOfWork(session) as unit_of_work:
            await unit_of_work.notes.add(Note(id=uuid4(), content="example"))

    transaction.rollback.assert_awaited_once_with()


async def test_commit_outside_context_is_an_error() -> None:
    session, _ = make_session()

    with pytest.raises(RuntimeError, match="Transaction is not active"):
        await PostgresNoteUnitOfWork(session).commit()

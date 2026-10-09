from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infra.storage.notes import PostgresNoteUnitOfWork
from app.services.notes import NoteUnitOfWork
from tests.contracts.note_unit_of_work import NoteUnitOfWorkContract, UnitOfWorkFactory

pytestmark = pytest.mark.integration


class TestPostgresNoteUnitOfWork(NoteUnitOfWorkContract):
    @pytest.fixture
    async def unit_of_work_factory(self, postgres_dsn: str) -> AsyncIterator[UnitOfWorkFactory]:
        engine = create_async_engine(postgres_dsn)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        opened: list[AsyncSession] = []

        def factory() -> NoteUnitOfWork:
            session = sessions()
            opened.append(session)
            return PostgresNoteUnitOfWork(session)

        yield factory
        for session in opened:
            await session.close()
        await engine.dispose()

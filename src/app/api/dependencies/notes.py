from collections.abc import AsyncIterator

from app.api.dependencies.storage import Storage, acquire
from app.infra.storage.base import POSTGRES_ORM
from app.services.notes import NoteUnitOfWork


async def get_note_unit_of_work(storage: Storage) -> AsyncIterator[NoteUnitOfWork]:
    """Yield a note unit of work backed by a request-scoped ORM session."""
    factory = await acquire(storage, POSTGRES_ORM)
    from app.infra.storage.notes import PostgresNoteUnitOfWork  # noqa: PLC0415 - optional extra

    async with factory() as session:
        yield PostgresNoteUnitOfWork(session)

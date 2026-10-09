from types import TracebackType
from typing import Self
from uuid import UUID

from sqlalchemy import String
from sqlalchemy.ext.asyncio import AsyncSession, AsyncSessionTransaction
from sqlalchemy.orm import Mapped, mapped_column

from app.core.metrics import observe_database_operation
from app.infra.storage.models import Base
from app.services.notes import Note


class NoteRow(Base):
    """Map notes to the example PostgreSQL table."""

    __tablename__ = "example_notes"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(String(500), nullable=False)


class PostgresNoteRepository:
    """Persist notes through a request-scoped SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, note: Note) -> None:
        """Flush a new note into the active transaction."""
        async with observe_database_operation("postgres_orm", "notes.insert"):
            self._session.add(NoteRow(id=note.id, content=note.content))
            await self._session.flush()

    async def get(self, note_id: UUID) -> Note | None:
        """Read a note through the active session."""
        async with observe_database_operation("postgres_orm", "notes.get"):
            row = await self._session.get(NoteRow, note_id)
        return Note(id=row.id, content=row.content) if row is not None else None


class PostgresNoteUnitOfWork:
    """Commit note changes explicitly and roll back uncommitted changes on exit."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._transaction: AsyncSessionTransaction | None = None
        self.notes = PostgresNoteRepository(session)

    async def __aenter__(self) -> Self:
        self._transaction = await self._session.begin()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._transaction is not None and self._transaction.is_active:
            await self._transaction.rollback()

    async def commit(self) -> None:
        """Commit the active transaction and record its metrics."""
        if self._transaction is None:
            raise RuntimeError("Transaction is not active")
        async with observe_database_operation("postgres_orm", "notes.commit"):
            await self._transaction.commit()

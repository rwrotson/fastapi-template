from collections.abc import Awaitable, Callable
from types import TracebackType
from typing import Self
from unittest.mock import AsyncMock
from uuid import UUID

from app.infra.storage.base import StorageHandle
from app.services.notes import Note


class FakeNotes:
    """In-memory note store shared by every `FakeUnitOfWork` built on it."""

    def __init__(self) -> None:
        self.committed: dict[UUID, Note] = {}
        self.pending: dict[UUID, Note] = {}

    async def add(self, note: Note) -> None:
        """Stage a note until the next commit."""
        self.pending[note.id] = note

    async def get(self, note_id: UUID) -> Note | None:
        """Read staged or committed notes."""
        return self.pending.get(note_id) or self.committed.get(note_id)


class FakeUnitOfWork:
    """Mirror `PostgresNoteUnitOfWork`: uncommitted changes are dropped on exit."""

    def __init__(self, notes: FakeNotes | None = None) -> None:
        self.notes = notes if notes is not None else FakeNotes()
        self.commits = 0

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.notes.pending.clear()

    async def commit(self) -> None:
        """Publish staged notes to the shared store."""
        self.notes.committed.update(self.notes.pending)
        self.notes.pending.clear()
        self.commits += 1


def make_handle(
    client: object,
    check: Callable[[], Awaitable[None]] | None = None,
    close: Callable[[], Awaitable[None]] | None = None,
) -> StorageHandle:
    """Wrap a fake client in a handle whose lifecycle calls are mocks by default."""
    return StorageHandle.of(client, check=check or AsyncMock(), close=close or AsyncMock())

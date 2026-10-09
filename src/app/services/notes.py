from dataclasses import dataclass
from types import TracebackType
from typing import Protocol, Self
from uuid import UUID, uuid4

from app.services.errors import NotFoundError


@dataclass(frozen=True, slots=True)
class Note:
    """Represent a persisted note independently of its storage adapter."""

    id: UUID
    content: str


class NoteNotFoundError(NotFoundError):
    """Identify a note requested by ID that does not exist."""

    def __init__(self, note_id: UUID) -> None:
        self.note_id = note_id
        super().__init__(f"Note {note_id} was not found")


class NoteRepository(Protocol):
    """Store and retrieve notes within a unit of work."""

    async def add(self, note: Note) -> None:
        """Stage a note in the current unit of work."""
        ...

    async def get(self, note_id: UUID) -> Note | None:
        """Find a note, including changes staged in the current unit of work."""
        ...


class NoteUnitOfWork(Protocol):
    """Manage a note transaction whose changes require an explicit commit."""

    @property
    def notes(self) -> NoteRepository:
        """Expose the repository bound to this transaction."""
        ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None:
        """Persist changes made in this unit of work."""
        ...


async def create_note(content: str, unit_of_work: NoteUnitOfWork) -> Note:
    """Create and commit a note."""
    note = Note(id=uuid4(), content=content)
    async with unit_of_work:
        await unit_of_work.notes.add(note)
        await unit_of_work.commit()
    return note


async def get_note(note_id: UUID, unit_of_work: NoteUnitOfWork) -> Note:
    """Retrieve a note or raise a service error when it is absent."""
    async with unit_of_work:
        note = await unit_of_work.notes.get(note_id)
    if note is None:
        raise NoteNotFoundError(note_id)
    return note

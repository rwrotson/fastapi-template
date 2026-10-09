from uuid import uuid4

import pytest

from app.services.notes import NoteNotFoundError, create_note, get_note
from tests.contracts.note_unit_of_work import NoteUnitOfWorkContract, UnitOfWorkFactory
from tests.fakes import FakeNotes, FakeUnitOfWork


class TestFakeNoteUnitOfWork(NoteUnitOfWorkContract):
    @pytest.fixture
    def unit_of_work_factory(self) -> UnitOfWorkFactory:
        notes = FakeNotes()
        return lambda: FakeUnitOfWork(notes)


async def test_create_note_commits_once() -> None:
    unit_of_work = FakeUnitOfWork()

    note = await create_note("example", unit_of_work)

    assert note.content == "example"
    assert unit_of_work.commits == 1
    assert unit_of_work.notes.committed == {note.id: note}


async def test_get_note_returns_stored_note_without_commit() -> None:
    unit_of_work = FakeUnitOfWork()
    note = await create_note("example", unit_of_work)

    assert await get_note(note.id, unit_of_work) == note
    assert unit_of_work.commits == 1


async def test_get_missing_note_raises_not_found() -> None:
    missing_id = uuid4()

    with pytest.raises(NoteNotFoundError) as error:
        await get_note(missing_id, FakeUnitOfWork())

    assert error.value.note_id == missing_id

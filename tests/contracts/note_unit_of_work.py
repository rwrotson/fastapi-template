from collections.abc import Callable
from uuid import uuid4

import pytest

from app.services.notes import Note, NoteUnitOfWork

type UnitOfWorkFactory = Callable[[], NoteUnitOfWork]


class NoteUnitOfWorkContract:
    """Check transaction behavior shared by fake and PostgreSQL note adapters."""

    async def test_committed_note_is_visible_to_a_new_unit_of_work(
        self, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        note = Note(id=uuid4(), content="committed")
        async with unit_of_work_factory() as unit_of_work:
            await unit_of_work.notes.add(note)
            await unit_of_work.commit()

        async with unit_of_work_factory() as unit_of_work:
            assert await unit_of_work.notes.get(note.id) == note

    async def test_added_note_is_visible_before_commit(
        self, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        note = Note(id=uuid4(), content="pending")
        async with unit_of_work_factory() as unit_of_work:
            await unit_of_work.notes.add(note)
            assert await unit_of_work.notes.get(note.id) == note

    async def test_uncommitted_note_is_discarded(
        self, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        note = Note(id=uuid4(), content="uncommitted")
        async with unit_of_work_factory() as unit_of_work:
            await unit_of_work.notes.add(note)

        async with unit_of_work_factory() as unit_of_work:
            assert await unit_of_work.notes.get(note.id) is None

    async def test_failed_block_discards_note(
        self, unit_of_work_factory: UnitOfWorkFactory
    ) -> None:
        note = Note(id=uuid4(), content="failed")

        async def fail_after_add() -> None:
            async with unit_of_work_factory() as unit_of_work:
                await unit_of_work.notes.add(note)
                raise RuntimeError("use case failed")

        with pytest.raises(RuntimeError, match="use case failed"):
            await fail_after_add()

        async with unit_of_work_factory() as unit_of_work:
            assert await unit_of_work.notes.get(note.id) is None

    async def test_missing_note_is_none(self, unit_of_work_factory: UnitOfWorkFactory) -> None:
        async with unit_of_work_factory() as unit_of_work:
            assert await unit_of_work.notes.get(uuid4()) is None

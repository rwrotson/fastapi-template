from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies.notes import get_note_unit_of_work
from app.api.errors import problem_responses
from app.services.notes import Note, NoteUnitOfWork, create_note, get_note

router = APIRouter(prefix="/notes", tags=["notes"])

UnitOfWork = Annotated[NoteUnitOfWork, Depends(get_note_unit_of_work, scope="function")]


class CreateNote(BaseModel):
    """Validate content for a new note."""

    content: str = Field(min_length=1, max_length=500)


class NoteResponse(BaseModel):
    """Represent a note in HTTP responses."""

    id: UUID
    content: str


def to_response(note: Note) -> NoteResponse:
    """Map a service note to its HTTP response."""
    return NoteResponse(id=note.id, content=note.content)


@router.post("", status_code=201)
async def create(payload: CreateNote, unit_of_work: UnitOfWork) -> NoteResponse:
    """Create a note and return its ID and content."""
    return to_response(await create_note(payload.content, unit_of_work))


@router.get("/{note_id}", responses=problem_responses(404))
async def read(note_id: UUID, unit_of_work: UnitOfWork) -> NoteResponse:
    """Return a note by ID."""
    return to_response(await get_note(note_id, unit_of_work))

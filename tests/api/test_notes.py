from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.notes import get_note_unit_of_work
from app.infra.storage.base import StorageManager
from app.infra.storage.notes import PostgresNoteUnitOfWork
from tests.fakes import FakeUnitOfWork, make_handle


@pytest.fixture
def unit_of_work(app: FastAPI) -> FakeUnitOfWork:
    """Replace the note dependency with a shared in-memory unit of work."""
    fake = FakeUnitOfWork()
    app.dependency_overrides[get_note_unit_of_work] = lambda: fake
    return fake


def test_notes_without_database_return_503(client: TestClient) -> None:
    response = client.post("/api/v1/notes", json={"content": "example"})

    assert response.status_code == 503
    assert response.json()["detail"] == "postgres_orm is not configured"


@pytest.mark.usefixtures("unit_of_work")
def test_empty_note_is_rejected(client: TestClient) -> None:
    assert client.post("/api/v1/notes", json={"content": ""}).status_code == 422


def test_created_note_can_be_read(client: TestClient, unit_of_work: FakeUnitOfWork) -> None:
    created = client.post("/api/v1/notes", json={"content": "example"})

    assert created.status_code == 201
    assert unit_of_work.commits == 1
    fetched = client.get(f"/api/v1/notes/{created.json()['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == created.json()


@pytest.mark.usefixtures("unit_of_work")
def test_missing_note_is_problem_404(client: TestClient) -> None:
    missing_id = uuid4()

    response = client.get(f"/api/v1/notes/{missing_id}")

    assert response.status_code == 404
    assert response.headers["Content-Type"] == "application/problem+json"
    assert response.json()["detail"] == f"Note {missing_id} was not found"


async def test_note_provider_uses_request_scoped_session() -> None:
    factory = MagicMock()
    manager = StorageManager()
    manager.handles["postgres_orm"] = make_handle(factory)

    provider = get_note_unit_of_work(manager)

    assert isinstance(await anext(provider), PostgresNoteUnitOfWork)
    with pytest.raises(StopAsyncIteration):
        await anext(provider)
    factory.return_value.__aexit__.assert_awaited_once()

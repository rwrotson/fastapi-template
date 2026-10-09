from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.config import PostgresOrmSettings, Settings
from app.main import create_app

pytestmark = pytest.mark.integration


def test_migrated_postgres_persists_notes_across_requests(postgres_dsn: str) -> None:
    orm = PostgresOrmSettings(dsn=SecretStr(postgres_dsn))
    settings = Settings(environment="test", postgres_orm=orm)
    content = f"integration-{uuid4()}"
    with TestClient(create_app(settings), base_url="http://localhost") as client:
        assert client.get("/ready").json()["dependencies"] == {"postgres_orm": "ok"}
        created = client.post("/api/v1/notes", json={"content": content})
        assert created.status_code == 201
        note = created.json()
        note_id = UUID(note["id"])
        assert note["content"] == content

        fetched = client.get(f"/api/v1/notes/{note_id}")
        assert fetched.status_code == 200
        assert fetched.json() == note
        assert client.get(f"/api/v1/notes/{uuid4()}").status_code == 404

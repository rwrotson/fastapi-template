from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.services.errors import ConflictError


def log_events(caplog: pytest.LogCaptureFixture) -> list[dict[str, object]]:
    """Extract structured events from captured log records."""
    return [record.msg for record in caplog.records if isinstance(record.msg, dict)]


def test_validation_error_is_problem_json(client: TestClient) -> None:
    response = client.post("/api/v1/examples/tasks", json={"message": ""})
    assert response.status_code == 422
    assert response.headers["Content-Type"] == "application/problem+json"
    problem = response.json()
    assert problem["title"] == "Unprocessable Content"
    assert problem["instance"] == "/api/v1/examples/tasks"
    assert problem["request_id"] == response.headers["X-Request-ID"]
    assert problem["errors"][0]["loc"] == ["body", "message"]


def test_unknown_route_is_problem_json(client: TestClient) -> None:
    response = client.get("/missing")
    assert response.status_code == 404
    assert response.json()["title"] == "Not Found"


def test_service_conflict_maps_to_409(app: FastAPI, client: TestClient) -> None:
    @app.get("/conflict")
    async def conflict() -> None:
        raise ConflictError("already exists")

    response = client.get("/conflict")
    assert response.status_code == 409
    assert response.json()["detail"] == "already exists"


def test_unhandled_error_is_logged_once_with_request_id(
    app: FastAPI, client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("secret internals")

    request_id = str(uuid4())
    response = client.get("/boom", headers={"X-Request-ID": request_id})

    assert response.status_code == 500
    assert response.headers["X-Request-ID"] == request_id
    assert "secret internals" not in response.text
    assert response.json()["request_id"] == request_id
    events = log_events(caplog)
    errors = [event for event in events if event["event"] == "unhandled_error"]
    assert len(errors) == 1
    assert errors[0]["request_id"] == request_id
    access = [event for event in events if event["event"] == "http_request"]
    assert access[-1]["status"] == 500


def test_access_log_skips_probes_and_records_client(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.clear()
    client.get("/live")
    client.get("/ready")
    client.get("/api/v1/examples/Ada")

    access = [e for e in log_events(caplog) if e["event"] == "http_request"]
    assert [event["route"] for event in access] == ["/api/v1/examples/{name}"]
    assert access[0]["client"] == "testclient"

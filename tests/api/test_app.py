from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.infra.storage.base import StorageManager
from app.main import create_app


def test_live(client: TestClient) -> None:
    assert client.get("/live").json() == {"status": "ok"}


def test_ready_without_backends(client: TestClient) -> None:
    assert client.get("/ready").json() == {"status": "ok", "dependencies": {}}


def test_greeting_example(client: TestClient) -> None:
    assert client.get("/api/v1/examples/Ada").json() == {"name": "Ada", "message": "Hello, Ada!"}


def test_background_task_example_is_accepted(client: TestClient) -> None:
    assert client.post("/api/v1/examples/tasks", json={"message": "hello"}).status_code == 202


@pytest.mark.parametrize(
    "expected",
    [
        'route="/api/v1/examples/{name}"',
        "app_http_request_duration_seconds_bucket",
        "app_http_requests_in_progress",
        "app_database_operations_total",
    ],
)
def test_metrics_expose_http_and_database_series(client: TestClient, expected: str) -> None:
    client.get("/api/v1/examples/Ada")

    metrics = client.get("/metrics")

    assert metrics.status_code == 200
    assert expected in metrics.text


@pytest.mark.parametrize(
    ("header", "value"),
    [
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "DENY"),
        ("Referrer-Policy", "no-referrer"),
    ],
)
def test_security_headers(client: TestClient, header: str, value: str) -> None:
    assert client.get("/live").headers[header] == value


def test_valid_request_id_is_echoed(client: TestClient) -> None:
    request_id = str(uuid4())
    response = client.get("/live", headers={"X-Request-ID": request_id})
    assert response.headers["X-Request-ID"] == request_id


def test_invalid_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/live", headers={"X-Request-ID": "invalid"})
    assert response.headers["X-Request-ID"] != "invalid"


def test_trusted_hosts() -> None:
    settings = Settings(environment="test", allowed_hosts=["example.test"])
    with TestClient(create_app(settings)) as client:
        assert client.get("/live").status_code == 400
        assert client.get("/live", headers={"Host": "example.test"}).status_code == 200
        assert client.get("/live", headers={"Host": "127.0.0.1"}).status_code == 200


def test_cors_preflight_allows_configured_origin_and_headers() -> None:
    settings = Settings(environment="test", cors_origins=["https://app.example"])
    with TestClient(create_app(settings), base_url="http://localhost") as client:
        response = client.options(
            "/api/v1/examples/Ada",
            headers={
                "Origin": "https://app.example",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == "https://app.example"
    assert "authorization" in response.headers["Access-Control-Allow-Headers"].lower()


def test_docs_follow_environment(client: TestClient) -> None:
    assert client.get("/docs").status_code == 200
    operations = {
        operation["operationId"]
        for path in client.get("/openapi.json").json()["paths"].values()
        for operation in path.values()
    }
    assert {"examples-greet", "notes-create", "notes-read", "health-live"} <= operations

    with TestClient(
        create_app(Settings(environment="production")), base_url="http://localhost"
    ) as production:
        assert production.get("/docs").status_code == 404
        assert production.get("/openapi.json").status_code == 404


def test_failed_startup_still_shuts_down_tracing(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = MagicMock()
    monkeypatch.setattr(main, "configure_tracing", lambda *_args: provider)
    monkeypatch.setattr(
        StorageManager, "open", AsyncMock(side_effect=RuntimeError("storage failed"))
    )
    application = create_app(Settings(environment="test"))

    with pytest.raises(RuntimeError, match="storage failed"), TestClient(application):
        pass

    provider.shutdown.assert_called_once_with()

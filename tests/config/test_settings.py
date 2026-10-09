import os
import re
from pathlib import Path
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies.config import get_config
from app.api.dependencies.storage import get_storage
from app.config import Settings, load_settings
from app.config.settings import env_fields
from app.infra.storage.base import StorageManager
from app.main import create_app

ENV_EXAMPLE = Path(__file__).parents[2] / ".env.example"


def add_probe(application: FastAPI) -> None:
    """Add a route that exposes the application's bound settings and storage identity."""

    @application.get("/_probe")
    def probe(
        config: Annotated[Settings, Depends(get_config)],
        storage: Annotated[StorageManager, Depends(get_storage)],
    ) -> dict[str, str]:
        return {"name": config.name, "storage": str(id(storage))}


def test_settings_use_code_defaults_and_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    defaults = load_settings()
    assert defaults.name == "FastAPI App"
    assert defaults.log_level == "INFO"
    assert defaults.postgres_orm is None
    assert defaults.allowed_hosts == ["localhost", "127.0.0.1"]

    monkeypatch.setenv("APP_NAME", "From environment")
    monkeypatch.setenv("APP_CLICKHOUSE__HOST", "clickhouse")
    monkeypatch.setenv("APP_CLICKHOUSE__PORT", "9000")
    monkeypatch.setenv("APP_REDIS__DSN", "redis://user:hunter2@redis:6379/0")
    configured = load_settings()
    assert configured.name == "From environment"
    assert configured.clickhouse is not None
    assert configured.clickhouse.port == 9000
    assert configured.redis is not None
    assert configured.redis.dsn.get_secret_value().endswith("@redis:6379/0")
    assert "hunter2" not in repr(configured)


def test_process_environment_overrides_dotenv(monkeypatch: pytest.MonkeyPatch) -> None:
    Path(".env").write_text("APP_NAME=From file\nAPP_LOG_LEVEL=WARNING\n")
    monkeypatch.setenv("APP_NAME", "From process")

    settings = Settings()

    assert settings.name == "From process"
    assert settings.log_level == "WARNING"


def test_environment_derived_defaults() -> None:
    development = Settings()
    assert development.resolved_log_format == "console"
    assert development.resolved_docs_enabled is True
    production = Settings(environment="production")
    assert production.resolved_log_format == "json"
    assert production.resolved_docs_enabled is False
    assert Settings(environment="production", docs_enabled=True).resolved_docs_enabled is True


def test_settings_and_storage_are_bound_per_application() -> None:
    first = create_app(Settings(environment="test", name="First"))
    second = create_app(Settings(environment="test", name="Second"))
    add_probe(first)
    add_probe(second)

    with (
        TestClient(first, base_url="http://localhost") as first_client,
        TestClient(second, base_url="http://localhost") as second_client,
    ):
        first_probe = first_client.get("/_probe").json()
        second_probe = second_client.get("/_probe").json()

    assert first_probe["name"] == "First"
    assert second_probe["name"] == "Second"
    assert first_probe["storage"] != second_probe["storage"]
    assert not first.dependency_overrides
    assert not second.dependency_overrides


def test_lifespan_preserves_test_dependency_overrides() -> None:
    application = create_app(Settings(environment="test"))
    replacement = Settings(environment="test", name="Overridden")
    application.dependency_overrides[get_config] = lambda: replacement
    add_probe(application)

    with TestClient(application, base_url="http://localhost") as client:
        assert client.get("/_probe").json()["name"] == "Overridden"

    assert application.dependency_overrides[get_config]() is replacement


def test_env_example_documents_every_setting() -> None:
    documented = set(re.findall(r"^#? ?(APP_[A-Z_]+)=", ENV_EXAMPLE.read_text(), re.MULTILINE))
    settings = {name for name, _ in env_fields()}
    assert settings - documented == set(), "add new settings to .env.example"
    assert documented - settings == {"APP_PORT"}, "remove stale settings from .env.example"


def test_no_app_variables_leak_into_tests() -> None:
    assert not [name for name in os.environ if name.startswith("APP_")]

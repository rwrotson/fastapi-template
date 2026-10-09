import logging
import os
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import structlog
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import Settings
from app.infra.storage import base
from app.main import create_app


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Keep the developer's APP_* variables and .env file out of every test."""
    for name in list(os.environ):
        if name.startswith("APP_"):
            monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)


@pytest.fixture(autouse=True)
def restore_logging() -> Iterator[None]:
    """Undo the global logging setup that every application lifespan performs."""
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    yield
    root.handlers, root.level = handlers, level
    structlog.reset_defaults()


@pytest.fixture
def settings() -> Settings:
    """Provide settings for an isolated test application."""
    return Settings(environment="test", readiness_cache_ttl=0)


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    """Create an application from the test settings."""
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Run an application lifespan for HTTP tests."""
    with TestClient(app, base_url="http://localhost") as test_client:
        yield test_client


@pytest.fixture
def fake_backends(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Replace all backend factories with one configurable mock."""
    create_handle = AsyncMock()
    monkeypatch.setattr(
        base, "import_module", lambda _: SimpleNamespace(create_handle=create_handle)
    )
    return create_handle

import json
import logging

import pytest
import structlog
from fastapi import FastAPI
from opentelemetry.sdk.trace import TracerProvider

from app.core.logging import configure_logging
from app.core.telemetry import configure_tracing


def test_json_logs_include_trace_context(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO", "json")
    tracer = TracerProvider().get_tracer("test")
    with tracer.start_as_current_span("work") as span:
        structlog.get_logger("test").info("inside_span", answer=42)
    structlog.get_logger("test").info("outside_span")

    inside, outside = (json.loads(line) for line in capsys.readouterr().out.splitlines())
    assert inside["event"] == "inside_span"
    assert inside["answer"] == 42
    assert inside["level"] == "info"
    assert inside["trace_id"] == format(span.get_span_context().trace_id, "032x")
    assert "trace_id" not in outside


def test_uvicorn_access_log_is_silenced() -> None:
    configure_logging("INFO", "json")
    assert not logging.getLogger("uvicorn.access").hasHandlers()
    assert logging.getLogger("uvicorn.error").hasHandlers()


def test_console_logs_are_human_readable(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("DEBUG", "console")
    logging.getLogger("stdlib").debug("from stdlib")

    output = capsys.readouterr().out
    assert "from stdlib" in output
    assert not output.lstrip().startswith("{")


def test_tracing_is_enabled_only_with_an_endpoint() -> None:
    assert configure_tracing(FastAPI(), None, "test") is None

    provider = configure_tracing(FastAPI(), "http://127.0.0.1:4318/v1/traces", "test")
    assert isinstance(provider, TracerProvider)
    assert provider.resource.attributes["service.name"] == "test"
    provider.shutdown()

import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter(
    "app_http_requests_total",
    "HTTP requests by method, route and status",
    ["method", "route", "status"],
)
HTTP_DURATION = Histogram(
    "app_http_request_duration_seconds",
    "HTTP request duration by method and route",
    ["method", "route"],
)
HTTP_IN_PROGRESS = Gauge(
    "app_http_requests_in_progress",
    "HTTP requests currently being handled",
)
STORAGE_AVAILABLE = Gauge(
    "app_storage_available",
    "Whether a configured storage backend passed its latest readiness probe",
    ["backend"],
)
DATABASE_OPERATIONS = Counter(
    "app_database_operations_total",
    "Database operations by backend, operation and result",
    ["backend", "operation", "result"],
)
DATABASE_DURATION = Histogram(
    "app_database_operation_duration_seconds",
    "Database operation duration by backend and operation",
    ["backend", "operation"],
)


@asynccontextmanager
async def observe_database_operation(backend: str, operation: str) -> AsyncIterator[None]:
    """Record an operation's duration and success or failure."""
    started = time.perf_counter()
    result = "ok"
    try:
        yield
    except Exception:
        result = "error"
        raise
    finally:
        DATABASE_OPERATIONS.labels(backend=backend, operation=operation, result=result).inc()
        DATABASE_DURATION.labels(backend=backend, operation=operation).observe(
            time.perf_counter() - started
        )

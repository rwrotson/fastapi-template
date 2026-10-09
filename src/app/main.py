from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from importlib.metadata import version
from typing import TypedDict

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import Response
from fastapi.routing import APIRoute
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.dependencies.storage import Storage
from app.api.errors import register_error_handlers
from app.api.health import router as health_router
from app.api.v1 import router as v1_router
from app.config import Settings, load_settings
from app.container import AppContainer
from app.core.logging import configure_logging
from app.core.middleware import RequestMiddleware
from app.core.telemetry import configure_tracing
from app.infra.storage.base import StorageManager

DISTRIBUTION = "fastapi-app"


class State(TypedDict):
    """Lifespan state shared with requests."""

    container: AppContainer


def operation_id(route: APIRoute) -> str:
    """Generate stable OpenAPI operation IDs such as `notes-create`."""
    return f"{route.tags[0]}-{route.name}" if route.tags else route.name


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build an application with isolated settings and storage lifecycle."""
    config = settings if settings is not None else load_settings()
    docs = config.resolved_docs_enabled

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[State]:
        configure_logging(config.log_level, config.resolved_log_format)
        try:
            async with AsyncExitStack() as cleanup:
                if tracer_provider is not None:
                    cleanup.callback(tracer_provider.shutdown)
                storage = StorageManager(
                    readiness_timeout=config.readiness_timeout,
                    readiness_cache_ttl=config.readiness_cache_ttl,
                )
                await storage.open(config)
                cleanup.push_async_callback(storage.close)
                structlog.get_logger().info("application_started", environment=config.environment)
                yield {"container": AppContainer(settings=config, storage=storage)}
        finally:
            structlog.get_logger().info("application_stopped")

    application = FastAPI(
        title=config.name,
        version=version(DISTRIBUTION),
        lifespan=lifespan,
        generate_unique_id_function=operation_id,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    allowed_hosts = sorted(set(config.allowed_hosts) | {"localhost", "127.0.0.1"})
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=config.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=config.cors_allow_headers,
        expose_headers=["X-Request-ID"],
    )
    application.add_middleware(GZipMiddleware, minimum_size=1000)
    application.add_middleware(RequestMiddleware)
    register_error_handlers(application)
    application.include_router(health_router)
    application.include_router(v1_router)

    @application.get("/metrics", include_in_schema=False)
    async def metrics(storage: Storage) -> Response:
        """Serve Prometheus metrics on the internal application port."""
        await storage.readiness()
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    tracer_provider = configure_tracing(application, config.otlp_endpoint, config.name)
    return application

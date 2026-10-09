import time
from uuid import UUID, uuid4

import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.metrics import HTTP_DURATION, HTTP_IN_PROGRESS, HTTP_REQUESTS
from app.core.problems import problem_response

QUIET_ROUTES = frozenset({"/live", "/ready", "/metrics"})


def request_id_from_header(value: str | None) -> str:
    """Accept UUID request IDs; replace all other input with a generated UUID."""
    if value is not None:
        try:
            return str(UUID(value))
        except ValueError:
            pass
    return str(uuid4())


def route_template(scope: Scope) -> str:
    """Return the matched route template, including router prefixes, for bounded labels."""
    # FastAPI's effective context retains prefixes omitted by included routers' routes.
    context = scope.get("fastapi", {}).get("effective_route_context")
    path = getattr(context, "path_format", None) or getattr(scope.get("route"), "path", None)
    return path if isinstance(path, str) else "unmatched"


class RequestMiddleware:
    """Attach request IDs, record bounded-cardinality telemetry and contain unexpected errors."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pass through non-HTTP scopes and instrument HTTP requests."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = request_id_from_header(Headers(scope=scope).get("x-request-id"))
        tokens = structlog.contextvars.bind_contextvars(request_id=request_id)
        logger = structlog.get_logger()
        started = time.perf_counter()
        status = 500
        response_started = False
        HTTP_IN_PROGRESS.inc()

        async def send_with_id(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                headers["X-Content-Type-Options"] = "nosniff"
                headers["X-Frame-Options"] = "DENY"
                headers["Referrer-Policy"] = "no-referrer"
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        except Exception:
            # Log inside the request context to retain its ID and avoid a second server log.
            logger.exception("unhandled_error", path=scope["path"])
            if response_started:
                raise
            await problem_response(500, instance=scope["path"])(scope, receive, send_with_id)
        finally:
            route_path = route_template(scope)
            method = scope["method"]
            elapsed = time.perf_counter() - started
            HTTP_REQUESTS.labels(method=method, route=route_path, status=str(status)).inc()
            HTTP_DURATION.labels(method=method, route=route_path).observe(elapsed)
            HTTP_IN_PROGRESS.dec()
            if route_path not in QUIET_ROUTES:
                client = scope.get("client")
                logger.info(
                    "http_request",
                    method=method,
                    route=route_path,
                    status=status,
                    duration=elapsed,
                    client=client[0] if client else None,
                )
            structlog.contextvars.reset_contextvars(**tokens)

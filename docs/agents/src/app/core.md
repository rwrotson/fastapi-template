# Core

- `src/app/core/` holds operational support and imports no business, HTTP-router, or infrastructure code.
- `logging.py`: `configure_logging()` routes stdlib and structlog records to stdout as JSON or console output and adds OpenTelemetry trace and span IDs. Lifespan calls it, so tests restore logging state.
- `middleware.py`: `RequestMiddleware` sets the request ID, writes the access log (route templates, not raw paths; `/live`, `/ready`, `/metrics` are quiet), and logs unhandled errors once.
- `problems.py`: the `Problem` model and `problem_response()` for RFC 9457 bodies.
- `metrics.py`: Prometheus collectors (`app_*` names). Labels use route templates and bounded operation names, never raw paths, IDs, or user data. Metrics are per process; the image runs one worker.
- `telemetry.py`: `configure_tracing()` is active only when `APP_OTLP_ENDPOINT` is set and skips probe and metrics routes.
- Update `docs/observability.md` when changing log fields, metrics, or tracing behavior.
- Ruff `banned-api` allows `logging.basicConfig`, `structlog.configure` and `logging.getLogger` only in `logging.py`; elsewhere use `structlog.get_logger()`.

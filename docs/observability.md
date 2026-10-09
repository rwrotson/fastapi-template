# Observability and HTTP settings

Each HTTP request receives a UUID `X-Request-ID`. A valid incoming UUID is preserved; other values are replaced. The ID is bound to structlog context and returned in the response. Responses also include `X-Content-Type-Options`, `X-Frame-Options`, and `Referrer-Policy` security headers; configure HSTS at the TLS reverse proxy. JSON access logs include method, route template (with router prefixes), status, duration, and client address. `/live`, `/ready`, and `/metrics` are measured but not access-logged. When tracing is active, every log record carries `trace_id` and `span_id`. Uvicorn's own access log is disabled, and unexpected exceptions are logged once as `unhandled_error` with the request ID. Set `APP_LOG_FORMAT=console` for readable local logs; it is the default in development. Paths are reported as route templates to prevent metric label cardinality from growing with path parameters.

`/metrics` publishes these application metrics:

| Metric | Meaning |
| --- | --- |
| `app_http_requests_total` | Completed requests by method, route template, and status |
| `app_http_request_duration_seconds` | Request latency histogram by method and route template |
| `app_http_requests_in_progress` | HTTP requests currently being handled |
| `app_storage_available` | Latest availability probe for each configured backend: 1 up, 0 down |
| `app_database_operations_total` | PostgreSQL note operations by operation name and result |
| `app_database_operation_duration_seconds` | Duration histogram for PostgreSQL note operations |

The Prometheus client also exposes its default Python and process metrics. `/metrics` runs the same bounded, concurrent storage probes as `/ready` before exporting, reusing a result younger than `APP_READINESS_CACHE_TTL`. Database operation metrics currently cover the notes adapter; add the same bounded operation names when adding other adapters. Avoid raw paths, IDs, query text, or user data in labels. `/metrics` shares the application port and must be restricted by the external reverse proxy. The production Compose file binds the application only to host localhost. The default container uses one worker, avoiding Prometheus multiprocess setup.

Set `APP_OTLP_ENDPOINT` to a full OTLP/HTTP trace endpoint such as `http://collector:4318/v1/traces` to enable FastAPI request spans. Probe and metrics routes are not traced. Otherwise tracing is inactive. The template does not run a collector.

`APP_CORS_ORIGINS` and `APP_ALLOWED_HOSTS` are JSON lists. By default, CORS allows no browser origins and trusted hosts allow localhost. Localhost and 127.0.0.1 remain allowed for container probes when you set a public hostname. Set explicit values for your domain and frontend; `APP_CORS_ALLOW_CREDENTIALS` and `APP_CORS_ALLOW_HEADERS` control credentialed requests and allowed headers, and `X-Request-ID` is exposed to browsers.

Errors use RFC 9457 `application/problem+json` bodies with `type`, `title`, `status`, `detail`, `instance`, and `request_id`; validation errors add an `errors` list. Unexpected errors become a generic 500 problem and are logged server-side. Swagger UI and OpenAPI are disabled in production unless `APP_DOCS_ENABLED=true`.

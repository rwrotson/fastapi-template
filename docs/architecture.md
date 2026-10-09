# Architecture and layer boundaries

The greeting endpoint uses a service without persistence. The optional notes feature connects a service port to a PostgreSQL adapter and an HTTP route.

| Layer | Location | Responsibility | Allowed inward imports |
| --- | --- | --- | --- |
| Services | `app/services/` | Use cases, their transport-independent types, errors, and ports (`Protocol` interfaces) | Services and Python standard library |
| HTTP interface | `app/api/v1/`, `app/api/errors.py` and other routers | Pydantic wire schemas, status codes, error mapping, auth and thin HTTP handlers | Services and result types |
| Infrastructure | `app/infra/` (`storage/` for the current clients) | External clients, connection lifecycle, readiness, and concrete adapters for service ports | Service ports, types, and configuration |
| Composition | `app/main.py`, `app/container.py`, and `app/api/dependencies/` | Build the FastAPI app and connect HTTP dependencies to concrete adapters | All layers as needed |
| Configuration | `app/config/` | Typed Pydantic Settings, environment loading, and code defaults | No business-layer dependency |
| Shared operational support | `app/core/` | Logging, ASGI middleware, problem details, metrics, and tracing | No business-layer, HTTP-router, or infrastructure dependency |

Business dependencies follow **HTTP → services ← infrastructure**. Services define ports without importing FastAPI, settings, or database drivers. Infrastructure implements those ports without importing HTTP code. `app/main.py` and `app/api/dependencies/` connect the layers; routers call use cases through that wiring.

Import-linter checks these boundaries with `uv run poe lint-imports`; contracts are in `pyproject.toml`.

`app.config.Settings` holds defaults in code and reads `APP_*` values from `.env` and the process environment. `create_app()` loads a fresh settings instance unless one is supplied explicitly. During lifespan, it opens the storage manager and yields an `AppContainer` with settings and storage as lifespan state, which Starlette copies into each `request.state`. HTTP providers resolve that container from the current `Request`, so two application instances have separate resources. Lifespan closes resources on shutdown, including after a failed startup. FastAPI `dependency_overrides` remain available to tests and are never changed by startup code.

## A request through the layers

1. An `app/api/` router validates HTTP input and calls a use case in `app/services/`. It maps the returned value to a Pydantic response model. Expected failures are raised as service errors (`NotFoundError`, `ConflictError`) and rendered by `app/api/errors.py` as RFC 9457 `application/problem+json` responses with the request ID.
2. The use case applies business rules. If it needs persistence, it accepts a port defined in `app/services/`, not a driver client.
3. An adapter in `app/infra/storage/` implements the port. A dependency in `app/api/dependencies/` constructs or retrieves that adapter from lifespan-managed clients through the storage provider.
4. `app/main.py` owns process-level setup and shutdown. The operational `/live`, `/ready`, and `/metrics` routes may access infrastructure state directly because they are not business use cases.

The `GET /api/v1/examples/{name}` route calls `app.services.greeting.greeting_message()` and maps the result to its HTTP `Greeting` schema. The optional `POST /api/v1/notes` and `GET /api/v1/notes/{note_id}` routes demonstrate persistence. The notes use cases depend on `NoteUnitOfWork`, a protocol defined in `app/services/notes.py`; the PostgreSQL implementation lives in `app/infra/storage/notes.py`. The HTTP dependency imports that implementation only when the ORM backend is configured.

## Adding a feature

- Put use cases and their transport-independent rules and types in `app/services/`.
- Define a `Protocol` beside the use case when it needs persistence or an external service. Express it in service terms, without driver types.
- Implement that port in `app/infra/storage/` or another `app/infra/` package. Register its client lifecycle in the app lifespan and expose the adapter through `app/api/dependencies/`.
- Add request/response schemas and a thin router in `app/api/v1/`, and include it in `app/api/v1/__init__.py`. Document extra error statuses with `problem_responses(404)`. Test use-case behavior without FastAPI or a database; test the HTTP mapping separately.

The notes feature spans `app/services/notes.py` (types and use cases), `app/infra/storage/notes.py` (persistence), `app/api/dependencies/notes.py` (session wiring), and `app/api/v1/notes.py` (HTTP mapping).

## Resource and transaction ownership

- `app/infra/storage/` creates configured clients and registers cleanup as each client is created. The app lifespan owns the manager and closes it on shutdown or failed startup. A failed close is logged while cleanup continues for the other clients.
- Each backend is a typed `BackendSpec` in `app/infra/storage/base.py`; `StorageManager.get(SPEC)` returns its client and owns the lifecycle. HTTP providers built with `require(SPEC)` or `acquire(storage, SPEC)` use it, translate missing or unavailable resources into 503 responses, and acquire request-scoped sessions. A use case decides which operations form one transaction; the concrete adapter or unit of work performs the commit or rollback. Do not commit inside each CRUD method.
- `create_note()` calls `commit()` before the route returns its 201 response. The PostgreSQL unit of work rolls back any still-active transaction on exit, including after an exception. Its dependency closes the session before the response is sent. The general `get_postgres_session()` dependency still only yields and closes a session; features using it must define their own transaction boundary.

Keep optional storage extras optional. Adding a feature must not make the base app require a database or credentials at startup.

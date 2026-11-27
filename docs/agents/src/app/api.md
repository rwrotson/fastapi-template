# API

- `src/app/main.py` defines the `create_app()` factory (run with `uvicorn app.main:create_app --factory`) and owns lifespan startup and shutdown. Lifespan yields the `AppContainer` as request state; HTTP providers read it from the current `Request`.
- `src/app/api/health.py` provides `/live` and dependency-aware `/ready`. `/live` never touches storage.
- Versioned routers and wire schemas live in `src/app/api/v1/` and are aggregated in `api/v1/__init__.py` (`/api/v1`). Keep routes thin: validate input, call a use case, map the result.
- Raise service errors instead of catching them; `src/app/api/errors.py` renders `NotFoundError` and `ConflictError` as RFC 9457 problem details. Document extra statuses with `problem_responses(404)`.
- `src/app/api/dependencies/` wires adapters: `get_container`, `get_config`, storage providers (`require(SPEC)`, `acquire(storage, SPEC)`), and the notes unit of work. A missing or unavailable backend yields a 503 problem response.
- `src/app/api/v1/auth.py` provides a fail-closed `get_current_principal`; authentication is not implemented.
- Routers import services and wire schemas, never infrastructure modules directly (the dependency layer does).
- Test status codes, response schemas, problem details, and behavior when an optional backend is absent. See the [test guide](../../tests.md).

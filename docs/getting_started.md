# Getting Started

## Run locally

Install uv (it provides the Python version in `.python-version`), then:

```bash
cp .env.example .env
uv sync --all-extras --all-groups
uv run poe serve
```

Open <http://127.0.0.1:8000/docs> or try:

```bash
curl http://127.0.0.1:8000/live
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/api/v1/examples/Ada
curl -X POST http://127.0.0.1:8000/api/v1/examples/tasks -H 'Content-Type: application/json' -d '{"message":"hello"}'
```

The example task only logs the message after the response; it does not persist work.

To try the persistent notes example, start PostgreSQL with `docker compose -f compose.yml -f compose.dev.yml --profile postgres up -d postgres`, install the `postgres-orm` extra, set `APP_POSTGRES_ORM__DSN=postgresql+psycopg://app:app@localhost:5432/app`, run `uv run poe migrate`, and start the app. `POST /api/v1/notes` accepts `{"content":"hello"}` and returns an ID for `GET /api/v1/notes/{note_id}`. These routes return 503 when PostgreSQL ORM is not configured, and an unknown ID returns a 404 problem response.

## Quality checks

```bash
uv run poe check         # fmt-check, lint, lint-imports, typecheck, test
uv run poe test-fast     # tests without coverage
uv run --all-extras --group docs mkdocs build --strict
uv run pre-commit install
```

Tests run in random order (pytest-randomly prints the seed; reproduce a failure with `uv run poe test-fast --randomly-seed=<seed>`). Integration tests need a migrated database. Run them with `APP_POSTGRES_ORM__DSN=... uv run poe test-integration`. Without the variable they are skipped in a normal run and fail fast when selected explicitly.

## Add a route

Put transport-independent business rules, types, and use cases in `src/app/services/`. Create a thin router under `src/app/api/v1/` with Pydantic request and response models, then include it in the versioned router in `src/app/api/v1/__init__.py`. If the use case needs storage, define its port beside the use case and wire an infrastructure adapter through `src/app/api/dependencies/`. Raise a service error such as `NotFoundError` for expected failures; the error handlers turn it into a problem response. See the [architecture guide](architecture.md) for the import rules and request flow.

The `get_current_principal` dependency in `src/app/api/v1/auth.py` returns 401 until you implement authentication. Use it on protected routes only after defining a real identity provider and authorization rules.

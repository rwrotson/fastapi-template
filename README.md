# fastapi-template

A GitHub template for a typed FastAPI service. It starts without a database and provides optional async clients for PostgreSQL, ClickHouse, MongoDB, and Redis.

## What is included

- FastAPI app factory, Pydantic Settings, JSON logs with request and trace IDs, Prometheus metrics, optional OpenTelemetry traces
- `/api/v1` example routes, an optional transactional PostgreSQL notes example, `/live` and dependency-aware `/ready`, RFC 9457 problem details for errors, OpenAPI at `/docs` outside production
- Strict MyPy, Ruff, import-linter layer contracts, pytest with a 95% coverage gate and random test order, a lowest-dependency test job, uv, poethepoet, pre-commit, Commitizen
- Multi-stage Docker image with cached dependency layers, hot reload Compose with optional database profiles, VPS Compose with log rotation and a migration service
- Release images for amd64 and arm64 on GHCR, ProperDocs reference on GitHub Pages

## Quick start

Requires [uv](https://docs.astral.sh/uv/); it installs the Python version from `.python-version`.

```bash
cp .env.example .env
uv sync --all-extras --all-groups
uv run poe serve
curl http://127.0.0.1:8000/live
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/api/v1/examples/Ada
```

`--all-extras` installs every optional integration. Install only the extras a service uses, for example `uv sync --extra postgres-orm`. Each enabled backend requires its matching extra; see [storage](docs/storage.md).

```bash
uv run poe check        # format check, lint, import contracts, type check, tests
uv run poe fmt          # rewrite formatting
uv run poe docs         # serve the docs locally (ProperDocs)
uv run pre-commit install
```

## Architecture

HTTP routes call use cases in `app.services`; infrastructure implements service ports and is wired through HTTP dependencies. Import contracts enforce these boundaries. The notes example includes a port, PostgreSQL adapter, and transaction; see [architecture](docs/architecture.md).

## Docker

For hot reload, optionally with local databases:

```bash
cp .env.example .env
docker compose -f compose.yml -f compose.dev.yml up --build
docker compose -f compose.yml -f compose.dev.yml --profile postgres up --build
```

For a VPS, set `IMAGE_REF=ghcr.io/OWNER/REPO:0.1.0` and the production settings in `.env`, then run `docker compose pull && docker compose up -d`. Set the repository variable `UV_SYNC_EXTRAS` before tagging if the release image needs storage extras. The service binds to `127.0.0.1:8000` on the host. Put your reverse proxy in front of that address and **block `/metrics`** from public access. See the [deployment guide](docs/deployment.md).

## Configuration

`app.config.Settings` defines defaults in code and reads `APP_*` environment variables and `.env`. Storage settings are nested with `__`, for example `APP_POSTGRES_ORM__DSN`; a backend is enabled when its DSN (or ClickHouse host) is set. Secrets are `SecretStr` values and are masked in logs and reprs. CORS defaults to no browser origins and trusted hosts default to localhost; add your external hostname to `APP_ALLOWED_HOSTS`. OpenAPI docs are disabled when `APP_ENVIRONMENT=production` unless `APP_DOCS_ENABLED=true`. See [.env.example](.env.example) and the generated configuration page in the documentation site.

## Use as a template

1. Select **Use this template** on GitHub and clone your new repository.
2. Change the distribution name in `pyproject.toml` and `DISTRIBUTION` in `src/app/main.py`, the project title in README and `properdocs.yml`, `APP_NAME`, and the GitHub URLs. Rename the `app` package only if your project needs a unique import name, and then update `module-name`, imports, import-linter, coverage, MyPy, and documentation generation together.
3. Choose storage extras, add your own API routers and models, and configure secrets in `.env` or your deployment secret store. Keep `.env` untracked.
4. Configure GitHub Pages to use GitHub Actions. A `v*` tag runs CI, then publishes the docs and a GHCR image. The VPS pull and Compose restart are manual.

### Remove the examples

The examples are meant to be copied, then deleted. When your first real feature exists, remove:

- greeting: `src/app/services/greeting.py`, `src/app/api/v1/examples.py`, its `include_router` line in `src/app/api/v1/__init__.py`, and the `/examples` assertions in `tests/api/test_app.py` and `tests/api/test_errors.py`
- notes: `src/app/services/notes.py`, `src/app/infra/storage/notes.py`, `src/app/api/dependencies/notes.py`, `src/app/api/v1/notes.py`, its `include_router` line, `migrations/versions/0001_example_notes.py`, the `NoteRow` import in `migrations/env.py`, the note fakes in `tests/fakes.py`, `tests/contracts/note_unit_of_work.py`, the `test_notes.py` files under `tests/services/`, `tests/api/`, and `tests/infra/`, and the note tests in `tests/integration/`
- the matching sections in `docs/architecture.md`, `docs/storage.md`, and `docs/getting_started.md`

Then run `uv run poe check`.

## Project layout

```text
src/app/services/       use cases, service types, errors, and ports for external services
src/app/api/            HTTP routes, schemas, error handlers, auth and dependency wiring
src/app/infra/storage/  optional client and repository adapters
src/app/config/         Pydantic Settings with environment overrides and code defaults
src/app/core/           logs, middleware, problem details, metrics, tracing
migrations/             optional PostgreSQL ORM Alembic environment
compose.yml             production VPS service and migration job
compose.dev.yml         development override with hot reload and database profiles
```

The `BackgroundTasks` example runs in process; queued work can be lost when the process stops.

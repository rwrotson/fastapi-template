# fastapi-template

A GitHub template for a typed FastAPI service. It starts without a database and provides optional async clients for PostgreSQL, ClickHouse, MongoDB, and Redis.

## What Is Included

- FastAPI app factory, Pydantic Settings, JSON logs with request and trace IDs, Prometheus metrics, optional OpenTelemetry traces
- `/api/v1` example routes, an optional transactional PostgreSQL notes example, `/live` and dependency-aware `/ready`, RFC 9457 problem details for errors, OpenAPI at `/docs` outside production
- Strict MyPy, Ruff, import-linter layer contracts, pytest with a 95% coverage gate, parallel (xdist) random-order runs, and sockets blocked outside live tests, a lowest-dependency test job, uv, poethepoet, pre-commit, Commitizen
- Multi-stage Docker image with cached dependency layers, hot reload Compose with optional database profiles, VPS Compose with log rotation and a migration service
- Release images for amd64 and arm64 on GHCR, ProperDocs reference on GitHub Pages

## Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** + **[Uvicorn](https://www.uvicorn.org/)** — async web framework and server
- **[Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)** — environment-based configuration
- **[structlog](https://www.structlog.org/)** — structured JSON logs; console output in development
- **[SQLAlchemy](https://www.sqlalchemy.org/)** + **[Alembic](https://alembic.sqlalchemy.org/)** — optional PostgreSQL ORM and migrations
- **[Prometheus client](https://prometheus.github.io/client_python/)** + **[OpenTelemetry](https://opentelemetry.io/)** — metrics and optional traces
- **[uv](https://docs.astral.sh/uv/)** — package management and build backend
- **[Ruff](https://docs.astral.sh/ruff/)** — linting and formatting
- **[MyPy](https://mypy.readthedocs.io/)** — strict type checking
- **[pytest](https://docs.pytest.org/)** + **[pytest-xdist](https://github.com/pytest-dev/pytest-xdist)** + **[pytest-randomly](https://github.com/pytest-dev/pytest-randomly)** — parallel tests in random order with coverage enforcement
- **[import-linter](https://import-linter.readthedocs.io/)** — layer boundary contracts
- **[poethepoet](https://poethepoet.natn.io/)** — task runner
- **[commitizen](https://commitizen-tools.github.io/commitizen/)** — Conventional Commits + automated versioning and CHANGELOG
- **[ProperDocs](https://properdocs.org/)** + **[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)** — documentation site

## Requirements

- Python 3.14+ (uv installs the version from `.python-version`)
- [uv](https://docs.astral.sh/uv/)
- Docker with Compose, optional, for containers and local databases

## Getting Started


```bash
cp .env.example .env
uv sync --all-extras --all-groups
uv run poe serve
curl http://127.0.0.1:8000/live
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/api/v1/examples/Ada
```

`--all-extras` installs every optional integration. Install only the extras a service uses, for example `uv sync --extra postgres-orm`. Each enabled backend requires its matching extra; see [storage](docs/storage.md).

## Usage

```bash
curl http://127.0.0.1:8000/live
curl http://127.0.0.1:8000/ready
curl http://127.0.0.1:8000/api/v1/examples/Ada
```

The OpenAPI schema is served at `/docs` outside production. See [architecture](docs/architecture.md) for the request flow and [storage](docs/storage.md) for the optional backends.

## Architecture

HTTP routes call use cases in `app.services`; infrastructure implements service ports and is wired through HTTP dependencies. Import contracts enforce these boundaries. The notes example includes a port, PostgreSQL adapter, and transaction; see [architecture](docs/architecture.md).

## Development

Run development tasks with [poethepoet](https://poethepoet.natn.io/):

```bash
uv run poe check        # format check, lint, import contracts, type check, tests
uv run poe quick        # lint, import contracts, type check
uv run poe test-live    # tests/integration against PostgreSQL (needs APP_POSTGRES_ORM__DSN)
uv run poe fmt          # rewrite formatting
uv run poe docs         # serve the docs locally (ProperDocs)
uv run pre-commit install
```

Claude Code hooks in `.claude/` format and autofix the Python file just edited and run `poe quick` at the end of a turn when Python files changed. Personal overrides go in `.claude/settings.local.json`, which is git-ignored.

## Docs

```bash
uv run --all-extras --group docs properdocs serve
uv run --all-extras --group docs properdocs build --strict
```

Source is in `docs/`. ProperDocs generates the API reference from public docstrings and the configuration page from `Settings`. The release workflow deploys the site to GitHub Pages.

## Versioning & Changelog

This template uses [Conventional Commits](https://www.conventionalcommits.org/) enforced by a `commit-msg` pre-commit hook.

```bash
uv run cz bump
git push origin main --tags

uv run cz changelog --dry-run
```

Bump type is inferred automatically: `fix:` → patch, `feat:` → minor, `feat!:` / `BREAKING CHANGE` → major (minor while the version is `0.x`). `cz bump` creates the tag locally; pushing it starts the release workflow.

## Configuration

`app.config.Settings` defines defaults in code and reads `APP_*` environment variables and `.env`. Storage settings are nested with `__`, for example `APP_POSTGRES_ORM__DSN`; a backend is enabled when its DSN (or ClickHouse host) is set. Secrets are `SecretStr` values; see [Credentials](#credentials). CORS defaults to no browser origins and trusted hosts default to localhost; add your external hostname to `APP_ALLOWED_HOSTS`. OpenAPI docs are disabled when `APP_ENVIRONMENT=production` unless `APP_DOCS_ENABLED=true`. See [.env.example](.env.example) and the generated configuration page in the documentation site.

## Credentials

Secret settings are `SecretStr` values, masked in logs and reprs. Set them in the untracked `.env` or in your deployment secret store, never in the repository. Each storage backend is enabled by its connection setting; install the matching extra first.

| Variable | How to obtain it |
| --- | --- |
| `APP_POSTGRES_ORM__DSN` | SQLAlchemy URL of a PostgreSQL database, `postgresql+psycopg://USER:PASSWORD@HOST:5432/DB`. Create the role and database (`CREATE ROLE ... LOGIN PASSWORD '...'`; `CREATE DATABASE ... OWNER ...`), or use the managed provider's connection string with the `+psycopg` driver. Also used by Alembic migrations |
| `APP_POSTGRES_RAW__DSN` | libpq DSN of a PostgreSQL database, `postgresql://USER:PASSWORD@HOST:5432/DB`, created the same way |
| `APP_CLICKHOUSE__PASSWORD` | Password of the ClickHouse user named in `APP_CLICKHOUSE__USERNAME`; set it with `ALTER USER ... IDENTIFIED BY '...'` or copy it from the managed service |
| `APP_MONGODB__DSN` | MongoDB connection string, `mongodb://USER:PASSWORD@HOST:27017/DB`; create the user with `db.createUser()` or copy the string from Atlas (Connect → Drivers) |
| `APP_REDIS__DSN` | Redis URL, `redis://:PASSWORD@HOST:6379/0` (`rediss://` for TLS); the password is the server's `requirepass` or the managed service's access key |

For local databases, `compose.dev.yml` profiles start services with the development credentials shown in `.env.example`. Do not reuse them in production. URL-encode special characters in passwords.

## Project Structure

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

## CI/CD

`.github/workflows/ci.yml` runs on every push and pull request. The `test` job runs on Ubuntu only because the service targets Linux. Jobs cover formatting, lint, import-linter contracts, strict MyPy, tests with a 95% coverage gate, tests against the lowest allowed direct dependencies, a migrated PostgreSQL integration test with `alembic check`, package, docs, and container builds with a container smoke test, a dependency audit, and an image vulnerability scan (CRITICAL/HIGH with an available fix).

`.github/workflows/release.yml` runs on version tags (`v*`) or via `workflow_dispatch`. It runs CI first and checks that the tag matches the project version. Tags then publish an amd64/arm64 image to GHCR and the ProperDocs site to GitHub Pages; manual runs only build and scan the image. Set Pages Source to **GitHub Actions** and allow `v*` tags in the `github-pages` environment.

## Docker and Deployment

For hot reload, optionally with local databases:

```bash
cp .env.example .env
docker compose -f compose.yml -f compose.dev.yml up --build
docker compose -f compose.yml -f compose.dev.yml --profile postgres up --build
```

For a VPS, set `IMAGE_REF=ghcr.io/OWNER/REPO:0.1.0` and the production settings in `.env`, then run `docker compose pull && docker compose up -d`. Set the repository variable `UV_SYNC_EXTRAS` before tagging if the release image needs storage extras. The service binds to `127.0.0.1:8000` on the host. Put your reverse proxy in front of that address and **block `/metrics`** from public access. See the [deployment guide](docs/deployment.md).

## Using This Template

1. Select **Use this template** on GitHub and clone your new repository.
2. Change the distribution name in `pyproject.toml` and `DISTRIBUTION` in `src/app/main.py`, the project title in README and `properdocs.yml`, `APP_NAME`, and the GitHub URLs. Rename the `app` package only if your project needs a unique import name, and then update `module-name`, imports, import-linter, coverage, MyPy, and documentation generation together.
3. Choose storage extras, add your own API routers and models, and configure secrets in `.env` or your deployment secret store. Keep `.env` untracked.
4. Configure GitHub Pages to use GitHub Actions. A `v*` tag runs CI (including a container smoke test), checks the tag against the project version, then publishes the docs and a GHCR image; manual release runs only build and scan the image. The VPS pull and Compose restart are manual.

See the [renaming checklist](docs/notes.md#renaming-the-template) for every file that carries the project name.

### Remove the Examples

The examples are meant to be copied, then deleted. When your first real feature exists, remove:

- greeting: `src/app/services/greeting.py`, `src/app/api/v1/examples.py`, its `include_router` line in `src/app/api/v1/__init__.py`, and the `/examples` assertions in `tests/api/test_app.py` and `tests/api/test_errors.py`
- notes: `src/app/services/notes.py`, `src/app/infra/storage/notes.py`, `src/app/api/dependencies/notes.py`, `src/app/api/v1/notes.py`, its `include_router` line, `migrations/versions/0001_example_notes.py`, the `NoteRow` import in `migrations/env.py`, the note fakes in `tests/fakes.py`, `tests/contracts/note_unit_of_work.py`, the `test_notes.py` files under `tests/services/`, `tests/api/`, and `tests/infra/`, and the note tests in `tests/integration/`
- the matching sections in `docs/architecture.md`, `docs/storage.md`, and `docs/getting_started.md`

Then run `uv run poe check`.

## Author

Igor Lashkov — rwrotson@yandex.ru

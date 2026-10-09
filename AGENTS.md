# Repository guide

This repository is a GitHub template for a FastAPI service. The distribution is `fastapi-app`, the import package is `app`, and Python 3.14+ is required.

## Commands

Use uv for dependencies and commands:

```bash
uv sync --all-extras --all-groups
uv run poe serve
uv run poe check          # fmt-check, lint, lint-imports, typecheck, test
uv run --all-extras --group docs mkdocs build --strict
```

Individual tasks: `fmt`, `fmt-check`, `lint`, `lint-imports`, `typecheck`, `test`, `test-fast` (no coverage), `test-integration`, `migrate`, `docs`, `audit`. CI runs formatting, lint, import-linter contracts, strict MyPy (including migrations), pytest with 95% coverage, tests against the lowest allowed direct dependencies, a migrated PostgreSQL integration test with `alembic check`, package/docs/container builds, dependency audit, and an image vulnerability scan.

## Dependencies

- Put runtime imports in project dependencies, optional backend drivers in the matching extra, development tools in `dev`, and documentation tools in `docs`.
- Change dependencies through uv and update `pyproject.toml` and `uv.lock` together. Verify the lock with `uv sync --locked --all-extras --all-groups`.
- Raise a direct dependency's lower bound when code needs a newer API. Verify new or upgraded dependencies against their declared lower bounds and the lowest-direct-dependencies CI job; the locked environment alone does not check them.
- Use the project environment for tools. Do not install packages manually into `.venv` or treat local installations as declared dependencies.

## Application structure

- `src/app/main.py` defines the `create_app()` factory (run with `uvicorn app.main:create_app --factory`) and owns lifespan startup and shutdown. Lifespan yields the `AppContainer` as request state.
- `src/app/api/health.py` provides `/live` and dependency-aware `/ready`.
- `src/app/services/` contains use cases, transport-independent types, errors (`NotFoundError`, `ConflictError`), and ports; it never imports FastAPI, settings, or database drivers. The notes example defines its `Note` type and unit-of-work port here.
- `src/app/api/v1/` contains versioned routers and wire schemas, aggregated in `api/v1/__init__.py`. Keep routes thin; raise service errors instead of catching them, because `src/app/api/errors.py` renders them as RFC 9457 problem details. `src/app/api/dependencies/` wires adapters.
- `src/app/config/` contains Pydantic Settings, `APP_*` environment loading, and defaults in code. Storage settings are nested models (`APP_REDIS__DSN`) with `SecretStr` secrets. `create_app()` owns one settings instance and lifespan binds it through a FastAPI dependency provider. Every setting must appear in `.env.example`; a test enforces it, and the docs configuration page is generated from `Settings`.
- `src/app/core/` contains logging, request middleware (request IDs, access log, unhandled errors), problem details, metrics, and optional tracing.
- `src/app/infra/storage/` contains optional async clients, readiness checks, and adapters for service ports. Backends are registered as `BackendSpec` entries in `base.py`; HTTP code gets clients with `require(SPEC)` or `acquire(storage, SPEC)`. The notes adapter uses PostgreSQL ORM and its initial migration. No storage service is required by default. A configured backend requires its matching project extra.
- `migrations/` is the optional Alembic environment for the `postgres-orm` extra.
- `tests/` mirrors the layers (`services/`, `api/`, `infra/`, `core/`, `config/`). Shared fakes live in `tests/fakes.py` and shared fixtures in `tests/conftest.py`. Use `fake_backends` to stub storage clients. Behaviour that every port adapter must share belongs in `tests/contracts/`. Run it against the fake in unit tests and against the real backend in `tests/integration/`; contract subclasses provide a `unit_of_work_factory` fixture whose instances share storage. Integration tests skip without `APP_POSTGRES_ORM__DSN` and fail when selected with `-m integration`.

Follow the import direction in `docs/architecture.md`: HTTP → services ← infrastructure, with infrastructure implementing ports defined in services. import-linter contracts in `pyproject.toml` enforce it. Use absolute `app.` imports and complete type annotations. Storage clients are initialized during lifespan, exposed to HTTP code through dependency providers, and closed at shutdown. A backend outage should affect `/ready`, not `/live` or process startup. Keep the default application usable without credentials or an external service.

## Change workflow

- Inspect `git status` before editing. Preserve existing uncommitted changes and limit edits to the requested task.
- Do not create Git commits. After completing and checking a meaningful, independently committable part of the work, pause and give the user a one-line Conventional Commit message in chat. Resume only after the user responds.
- Run `uv run poe check` after application code changes. After documentation source or public docstring changes, also run `uv run --all-extras --group docs mkdocs build --strict`.
- Do not lower coverage thresholds, disable checks, or add lint and type suppressions solely to pass CI. Explain necessary suppressions at the affected line.
- Use non-rewriting checks for verification; run formatters or `--fix` only when intentionally editing files. Pre-commit's Ruff hooks rewrite files.
- Add an Alembic revision for every ORM schema change. Verify it against a migrated PostgreSQL database with `alembic check` and the integration tests.
- Report which checks ran, which were skipped, and why. When no PostgreSQL DSN is configured, report integration tests as skipped rather than as full integration verification; `test-fast` is not the full CI suite.
- For endpoint changes, test status codes, response schemas, problem details, and behavior when an optional backend is absent.
- Keep mutable settings and storage state scoped to the application lifespan or request. Tests must pass in random order without depending on process-wide state.
- Edit `Settings` field descriptions and source docstrings, then rebuild MkDocs; do not edit generated configuration or API reference pages.

## Deployment and releases

The production image uses one Uvicorn worker, trusts proxy headers from `FORWARDED_ALLOW_IPS`, and logs to stdout. `compose.yml` binds the app to localhost on the VPS, rotates container logs, and has a `migrate` profile service; an external reverse proxy must block public access to `/metrics`. `compose.dev.yml` adds a hot reload development stage and optional database profiles. Version tags run CI, then publish an amd64/arm64 image to GHCR and MkDocs to GitHub Pages. The VPS update is manual.

The user's `.env` and secrets stay untracked. Update README, `.env.example`, and MkDocs when changing public settings, endpoints, storage extras, or deployment instructions.

## Documentation and comments

- Write documentation, docstrings, and comments in English. Keep them brief and factual; describe each entity's purpose and relevant behavior without lecturing or editorial commentary.
- Do not write module docstrings. Package docstrings in `__init__.py` are allowed. Describe package behavior and any module-level nuance in README, AGENTS.md, or MkDocs when it needs explanation.
- Give every public class, function, and method a docstring, preferably one line. Describe its overall purpose without repeating its name, signature, types, or obvious implementation. Test functions are identified by their names and do not need docstrings.
- Add docstrings to protected and private objects only when they explain important behavior that the code does not make clear.
- Keep inline comments only for non-obvious behavior, constraints, or decisions. Put a short comment on the relevant line when it fits; otherwise put it immediately above. Keep required tool directives such as `noqa`.
- Prefer clearer names and more precise types over comments that explain the code.

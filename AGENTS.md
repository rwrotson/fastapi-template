# AGENTS.md

A GitHub template for a typed FastAPI service with optional async storage clients, Prometheus metrics, and optional OpenTelemetry tracing.

Distribution name: `fastapi-app` | Python package: `app` | Environment prefix: `APP_`

## Load instructions by path

For each area of the task, mirror its repo-relative path under [docs/agents](docs/agents/) and read the matching guide before editing: for `src/app/infra/storage/base.py`, read the [infrastructure guide](docs/agents/src/app/infra.md). For any code change, also read [docs/architecture.md](docs/architecture.md); for any Python change, read the [Python style guide](docs/agents/python-style.md). A feature that spans layers gets its own `docs/agents/features/<name>.md`, read alongside the layer guides. The [Read when](#read-when) table lists every guide.

## Commands

This project uses [uv](https://docs.astral.sh/uv/) for package management; Python 3.14+ is required.

```bash
uv sync --all-extras --all-groups
uv run poe serve
uv run poe check            # fmt-check, lint, lint-imports, typecheck, test (95% branch coverage)
uv run poe quick            # lint, lint-imports, typecheck (no formatting check or tests)
uv run poe test-fast        # pytest without coverage, parallel, random order
uv run poe test-live        # tests/integration (--live) against PostgreSQL; needs APP_POSTGRES_ORM__DSN
uv run poe fmt              # ruff format . (rewrites files)
uv run poe migrate          # alembic upgrade head
uv run poe audit            # pip-audit over locked dependencies
uv run --all-extras --group docs properdocs build --strict
```

Other tasks: `fmt-check`, `lint`, `lint-imports`, `typecheck`, `test`, `docs`.

If the default uv cache is not writable (for example, in an agent sandbox) and dependencies are synced, run `UV_CACHE_DIR=<writable tmp dir> uv run --offline poe check`. A failed loopback request from a sandbox does not prove that a local server is down.

## Change Workflow

- Inspect `git status` before editing. Preserve existing uncommitted changes and limit edits to the requested task.
- When working from an active staged plan in `docs/plans/`, read it before work, implement only the first incomplete stage, append dated evidence, and stop at the stage boundary. Delete a plan once all its stages are done.
- Run `uv run poe check` after application code changes. After documentation, `properdocs.yml`, or public docstring changes, also run `uv run --all-extras --group docs properdocs build --strict`.
- The Claude Code hooks in `.claude/` run `ruff format` and `ruff check --fix` on the Python file just edited (an intentional edit) and, at Stop, run `poe quick` when Python files changed during the turn; they do not replace `poe check`.
- Use non-rewriting checks (`poe fmt-check`, `poe lint`) for verification; run formatters or `--fix` only when intentionally editing files. Pre-commit's Ruff hooks rewrite files.
- Report which checks ran, which were skipped, and why. Without `APP_POSTGRES_ORM__DSN`, report integration tests as not run (they are collected only by `poe test-live`), not as verified. `poe test-fast` is not the full CI suite: it skips coverage, and CI also runs the lowest-dependency job, a migrated PostgreSQL integration job, package, docs, and container builds, and security scans.
- When changing settings, endpoints, storage extras, or deployment, update `.env.example`, README, and the docs.
- Add an Alembic revision for every ORM schema change and verify it as described in the [migrations guide](docs/agents/migrations.md).

## Commit Handoff

- Do not create or amend commits on the user's behalf.
- After completing and verifying a meaningful, self-contained part of the work, pause before starting the next part.
- At each pause, send the user a one-line English Conventional Commit message for the completed work. Resume when the user asks you to continue.

## Layers

```
api       src/app/api/           HTTP routers, wire schemas, error handlers, dependency wiring
infra     src/app/infra/         storage clients, readiness checks, adapters for service ports
services  src/app/services/      use cases, transport-independent types, errors, ports
core      src/app/core/          logging, middleware, problem details, metrics, tracing
config    src/app/config/        Pydantic Settings and environment loading
```

`src/app/main.py` and `src/app/container.py` compose the layers. Dependencies follow HTTP → services ← infrastructure; infrastructure implements ports defined in services. The rules are in [docs/architecture.md](docs/architecture.md); `uv run poe lint-imports` enforces them.

## Invariants

- Do not lower coverage thresholds, disable checks, relax import-linter contracts, or add lint and type suppressions solely to pass CI. Explain necessary suppressions at the affected line.
- Services never import FastAPI, settings, or database drivers. Infrastructure never imports HTTP code.
- The default application must start and pass `/live` and `/ready` without credentials or an external service. A backend outage affects `/ready`, not `/live` or process startup.
- Keep mutable settings and storage state scoped to the application lifespan or request. Tests must pass in random order without depending on process-wide state.
- Expected failures raise a `ServiceError` subclass from services; `app/api/errors.py` renders them as RFC 9457 problem details.
- Tests never use the network, except `tests/integration/` under `--live`, which connects to the PostgreSQL database named by `APP_POSTGRES_ORM__DSN`.
- Every secret setting is a `SecretStr` and gets step-by-step instructions in a README "Credentials" section in the same change; secrets stay out of logs and reprs.
- Code, docs, comments, and commit messages are in English.
- Keep the user's `.env` and secrets untracked.

## Read when

| Task | Read |
| --- | --- |
| Any code change | [docs/architecture.md](docs/architecture.md) (layers, request flow, transactions) |
| Any Python change (imports, typing, formatting, docstrings, comments) | [Python style guide](docs/agents/python-style.md) |
| Working in `src/app/api/` or `src/app/main.py` | [API guide](docs/agents/src/app/api.md) |
| Working in `src/app/services/` | [Services guide](docs/agents/src/app/services.md) |
| Working in `src/app/infra/`, adding a storage backend or adapter | [Infrastructure guide](docs/agents/src/app/infra.md) |
| Working in `src/app/config/`, settings, `.env.example` | [Config guide](docs/agents/src/app/config.md) |
| Working in `src/app/core/` (logging, middleware, metrics, tracing) | [Core guide](docs/agents/src/app/core.md) |
| ORM models, `migrations/`, Alembic | [Migrations guide](docs/agents/migrations.md) |
| Working in `tests/` | [Test guide](docs/agents/tests.md) |
| Working in `docs/`, `properdocs.yml`, or public docstrings | [Docs guide](docs/agents/docs.md) |
| Dependencies, extras, `pyproject.toml`, `uv.lock` | [Dependency guide](docs/agents/pyproject.md) |
| CI, releases, Dependabot | [GitHub guide](docs/agents/github.md) |
| Dockerfile, Compose, VPS deployment | [Deployment guide](docs/agents/deployment.md) |
| Renaming the template | [Renaming checklist](docs/notes.md#renaming-the-template) |

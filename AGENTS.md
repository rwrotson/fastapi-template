# AGENTS.md

A GitHub template for a typed FastAPI service with optional async storage clients, Prometheus metrics, and optional OpenTelemetry tracing.

Distribution name: `fastapi-app` | Python package: `app` | Environment prefix: `APP_`

## Load instructions by path

For each area of the task, mirror its repo-relative path under [docs/agents](docs/agents/) and read the matching guide before editing: for `src/app/infra/storage/base.py`, read the [infrastructure guide](docs/agents/src/app/infra.md). For any code change, also read [docs/architecture.md](docs/architecture.md). The [Read when](#read-when) table lists every guide.

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

## Change Workflow

- Inspect `git status` before editing. Preserve existing uncommitted changes and limit edits to the requested task.
- When working from an active staged plan in `docs/plans/`, read it before work, implement only the first incomplete stage, append dated evidence, and stop at the stage boundary.
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

## Code Style

- Use absolute `app.` imports; Ruff bans relative imports.
- Import a module or package whose name starts with `_` only from modules in the same package and its subpackages.
- MyPy runs with `strict = true` and the Pydantic plugin over `src/`, `tests/`, `migrations/`, and `docs/`. All new code must have complete type annotations. Prefer `X | Y` over `Optional[X]`.
- Frozen models used as default argument values are registered in `[tool.ruff.lint.flake8-bugbear] extend-immutable-calls` in `pyproject.toml`.

## Python Formatting

- Keep function signatures, calls, and collection literals on one line when they fit. When they need wrapping, put one parameter, argument, or item on each line. Add a trailing comma after the last entry when there are two or more entries so Ruff preserves the layout. Do not enable `COM812`.
- Omit optional trailing commas in single-entry forms. Keep the required comma in a single-element tuple and any comma Ruff inserts in a wrapped signature with one parameter.

## Documentation and Comments

- Keep documentation, docstrings, and comments short and factual. Describe each entity's purpose without editorial commentary or tutorials.
- Do not add module docstrings. Package docstrings in `__init__.py` are optional. Put package behavior and important module details in Markdown documentation such as `README.md` or `docs/`.
- Give public classes, functions, and ordinary methods a docstring. Prefer one line describing their overall purpose; do not repeat names, signatures, or type annotations. Ruff checks these in application code. Test functions, fixtures, and standard `dunder` methods are exempt.
- Add docstrings to protected or private objects only when they explain behavior that is not clear from code.
- Keep inline comments only for non-obvious behavior or decisions. Put a short comment on the relevant line when it fits; otherwise place it immediately above. Retain necessary tool directives such as `# noqa` and `# type: ignore`.
- A comment placed above a line or group of lines applies only to it. Separate that line or group from the code before and after it with a blank line, unless it starts or ends a block, so the comment's scope is clear. At module and class level, give each commented constant or attribute its own block, and keep uncommented related definitions together in one block.
- In long functions, methods, and tests, separate logical steps (input validation, setup, execution, result handling; arrange, act, assert) with a single blank line. Do not add comments to label the steps. Keep short functions compact.
- At module level, keep `UPPER_CASE` constants and lowercase objects (loggers, imported modules, routers, apps) in separate blocks divided by a blank line.
- Prefer clearer names and more precise types over comments that restate code.
- Edit `Settings` field descriptions and source docstrings, then rebuild the docs; do not edit generated configuration or API reference pages.

## Read when

| Task | Read |
| --- | --- |
| Any code change | [docs/architecture.md](docs/architecture.md) (layers, request flow, transactions) |
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

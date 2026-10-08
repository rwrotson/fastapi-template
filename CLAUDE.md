# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A template for building Python CLI apps using [Typer](https://typer.tiangolo.com/) with Rich output, structlog-based structured logging, and Pydantic Settings-based configuration.

Distribution name: `cli-app` | Python package: `cli_app` | Entry point: `cli-app`

## Commands

This project uses [uv](https://docs.astral.sh/uv/) for package management.

```bash
# Install dependencies
uv sync --all-extras

# Run the CLI
uv run cli-app

# Tasks via taskipy (uv run task <name>)
uv run task lint        # ruff check .
uv run task fmt         # ruff format .
uv run task typecheck   # mypy src/
uv run task test        # pytest (parallel, 80% coverage enforced)
uv run task test-fast   # pytest --no-cov -n auto
uv run task audit       # pip-audit

# Or run tools directly
uv run ruff check .
uv run ruff format .
uv run mypy src/
uv run pytest
uv run pytest --no-cov

# Install pre-commit hooks
uv run pre-commit install

# Run pre-commit on all files
uv run pre-commit run --all-files

# Versioning
uv run cz bump           # bump version, update CHANGELOG, tag
uv run cz changelog      # update CHANGELOG only

# Serve docs locally (live reload)
uv run --group docs mkdocs serve

# Build static docs site (CI deploys this to GitHub Pages via actions/deploy-pages)
uv run --group docs mkdocs build
```

## CI/CD

`.github/workflows/ci.yml` triggers on push/PR to `main` and `dev`. One job:

- **`ci`** — ruff format check → ruff lint → mypy → pytest → pip-audit → trivy (CRITICAL/HIGH CVE scan).

`.github/workflows/release.yml` triggers on version tags (`v*`) and manual `workflow_dispatch`. One job:

- **`docs`** — builds the site with `mkdocs build` and deploys it to **GitHub Pages** via
  `actions/upload-pages-artifact` + `actions/deploy-pages` (the `github-pages` environment).
  Permissions: `pages: write`, `id-token: write`, `contents: read`. There is **no PyPI publish**.

Pages Source must be set to **"GitHub Actions"** (Settings → Pages), and the `github-pages`
environment must allow the `v*` tag (Settings → Environments → Deployment branches and tags → no
restriction, or a `v*` rule) — otherwise the tag-triggered deploy is blocked. Site:
https://rwrotson.github.io/typer-template/

Dependabot opens weekly PRs for pip packages and GitHub Actions (`.github/dependabot.yml`).

## Architecture

### Package Layout & Build

Source lives in `src/cli_app/` — the standard `src/` layout. The uv build backend is configured in `pyproject.toml`:

```toml
[tool.uv.build-backend]
module-name = "cli_app"
module-root = "src"
```

All internal imports are **absolute**, using the `cli_app.` prefix:

```python
from cli_app.cli.app import app
from cli_app.utils.console import get_console
```

### Entry Point & Startup

`src/cli_app/main.py` is minimal: calls `setup_logging()`, `get_console()`, then `app()`. The console script entry point is `cli_app.main:main`.

### CLI Structure

```
src/cli_app/cli/app.py          — Root Typer app; registers subcommand groups and global options
src/cli_app/cli/callbacks/      — Eager option callbacks that print metadata and exit
src/cli_app/cli/commands/       — Subcommand groups; each file creates its own Typer sub-app
```

The root callback (`app.py`) sets two values in `ctx.obj` before any subcommand runs:

- `ctx.obj["output_format"]` — `OutputFormat.text` or `OutputFormat.json` (from `--output-format`)
- Adjusts root logger level when `--verbose` is passed.

To add a new command group: create a file in `src/cli_app/cli/commands/`, define a Typer app, export it from `__init__.py`, then add `app.add_typer(...)` in `src/cli_app/cli/app.py`.

### Configuration via Environment Variables

`ConsoleConfig` (`src/cli_app/utils/console.py`) and `LogConfig` (`src/cli_app/utils/log.py`) are Pydantic `BaseSettings` classes that read from environment variables and `.env` files:

- Console: `CLI_APP_CONSOLE_*`
- Logging: `CLI_APP_LOG_*`

`get_console()` and `get_project_meta()` are `@cache`-decorated — call them anywhere without performance concern.

### Logging (structlog)

`setup_logging()` configures structlog bridged through stdlib via `ProcessorFormatter`. Both first-party (`structlog.get_logger()`) and third-party stdlib loggers share the same handler chain. Console output uses `ConsoleRenderer` by default; set `CLI_APP_LOG_USE_JSON_FORMATTER=true` for JSON. File output is always JSON.

Use `structlog.contextvars.bind_contextvars(key=value)` to attach context that appears on every log line.

Before `setup_logging()` is called (e.g. in tests), structlog defaults to stderr output so it never pollutes stdout.

### Utilities

| Module | Purpose |
|--------|---------|
| `src/cli_app/utils/console.py` | Singleton Rich `Console` with theming |
| `src/cli_app/utils/log.py` | structlog setup; file + console handlers; `LogConfig` Pydantic settings |
| `src/cli_app/utils/output.py` | `OutputFormat` enum; `render_output()` and `echo_json()` helpers |
| `src/cli_app/utils/stdin.py` | `is_stdin_piped()`, `read_stdin_if_piped()`, `iter_stdin_lines()` |
| `src/cli_app/utils/meta.py` | Reads distribution metadata at runtime; scans `direct_url.json` for editable-install compat |
| `src/cli_app/utils/format.py` | Rich `Theme` with `info`/`warning`/`danger` styles |
| `src/cli_app/utils/emoji.py` | `Emoji` StrEnum for consistent emoji usage |
| `src/cli_app/utils/progress.py` | Rich `Progress` bar wired to the project console |
| `src/cli_app/utils/misc.py` | `find_project_root()` helper |

### Type Checking

MyPy runs in strict mode (`disallow_untyped_defs = true`). All new code must have complete type annotations. Python 3.13+ union syntax (`X | Y`) is preferred over `Optional[X]`.

# Notes

## Build Backend

`uv_build` loads the `app` package from `src/`:

```toml
[tool.uv.build-backend]
module-name = "app"
module-root = "src"
```

The wheel includes `py.typed`, so type checkers use the package's inline annotations.

## structlog Integration

`app.core.logging.configure_logging()` connects [structlog](https://www.structlog.org/) to stdlib logging through `ProcessorFormatter`:

- Application and library modules use stdlib loggers or structlog; their records share one stdout handler.
- Logs are JSON lines, or colourised `ConsoleRenderer` output with `APP_LOG_FORMAT=console` (the default in development).
- Timestamps are ISO 8601 in UTC; the level and logger name are added to every event.
- When tracing is active, `trace_id` and `span_id` of the current OpenTelemetry span are added.
- `structlog.contextvars` fields are merged into every event; the request middleware binds the request ID this way.
- Uvicorn's loggers propagate to the root handler, and its access log is silenced because `RequestMiddleware` writes the access log.

Lifespan calls `configure_logging()`, which replaces the root handlers.

## Documentation Toolchain

The site is built with [ProperDocs](https://properdocs.org/), a maintained continuation of MkDocs 1.x that reads the same configuration (`properdocs.yml`) and runs MkDocs themes and plugins unchanged. MkDocs 2.0 drops the plugin and theme system, and Material for MkDocs requires `mkdocs<2`, so the `mkdocs` package stays on 1.x as a library dependency of the plugins. Running `properdocs` instead of `mkdocs` also avoids the MkDocs 2.0 warnings printed by Material and the plugins.

[Zensical](https://zensical.org/), the successor to Material for MkDocs, does not support `mkdocs-gen-files` yet; the API reference and configuration pages depend on it.

## Commitizen & Versioning

[Commitizen](https://commitizen-tools.github.io/commitizen/) reads Conventional Commit messages to select the next version and update `CHANGELOG.md`. Its settings are in `pyproject.toml`:

```toml
version_provider = "uv"
update_changelog_on_bump = true
major_version_zero = true
```

The `commit-msg` hook checks Conventional Commit format. A `v*` tag runs the release workflow, which publishes the image and the docs.

## Renaming the Template

Choose names before editing: a distribution name (for example, `my-service`), an import package (`my_service`, optional), an environment prefix (`MY_SERVICE_`, optional), and an image name.

1. Set `[project].name`, the description, authors, keywords, in `pyproject.toml`, `DISTRIBUTION` in `src/app/main.py`, and the default of `Settings.name`.
2. To rename the `app` package, rename `src/app/` and `docs/agents/src/app/`, then replace `app` in imports under `src/`, `tests/`, `migrations/`, and `docs/`, in `docs/gen_ref_pages.py` and `docs/gen_config_page.py`, and in `module-name` under `[tool.uv.build-backend]`, `[tool.coverage.run].source`, `[tool.ruff.lint.isort].known-first-party`, `[tool.importlinter]`, `[tool.poe.tasks]` (`serve`, `test`), the `uvicorn app.main:create_app` command in `Dockerfile`, `compose.yml`, and `compose.dev.yml`, and the `app` imports in `migrations/env.py`.
3. To change the `APP_` prefix, edit `env_prefix` in `src/app/config/settings.py`, the `APP_` default in `env_fields()` (`src/app/config/settings.py`), `.env.example`, `compose.yml`, `compose.dev.yml`, README, docs, and tests that set `APP_*` variables.
4. Update `properdocs.yml` (`site_name`, repository links, source watch path) and names and links in README, `docs/`, `AGENTS.md`, and `docs/agents/`. Update the copyright holder in `LICENSE`.
5. Update the image name in `compose.yml` (`IMAGE_REF` default), `.github/workflows/ci.yml` (`fastapi-app:ci`), and README and docs examples (`ghcr.io/OWNER/REPO`).
6. Configure GitHub Pages (Source: GitHub Actions; the `github-pages` environment must allow `v*` tags) and the `UV_SYNC_EXTRAS` repository variable.
7. Regenerate the lockfile with `uv lock`, then run `uv sync --locked --all-extras --all-groups`, `uv run poe check`, and `uv run --all-extras --group docs properdocs build --strict`.

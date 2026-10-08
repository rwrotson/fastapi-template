# Notes

## Build Backend

The project uses `uv_build` with the standard `src/` layout: source lives in `src/cli_app/`. This is the conventional approach and is configured with:

```toml
[tool.uv.build-backend]
module-name = "cli_app"
module-root = "src"
```

`module-root = "src"` tells uv_build to look for `./src/cli_app/__init__.py` as the package root.

## Package Metadata at Runtime

`src/cli_app/utils/meta.py` uses `importlib.metadata` to read the installed distribution's name, version, and dependencies. For editable installs (the default with `uv sync`), uv_build does not write a `top_level.txt`, so `packages_distributions()` cannot always map the `cli_app` package back to the `cli-app` distribution. Instead, `Meta.load_from_installed_package()` scans all installed distributions and finds the one whose `direct_url.json` points to a directory containing the current file.

## structlog Integration

Logging is built on [structlog](https://www.structlog.org/) bridged through stdlib's `logging` module via `ProcessorFormatter`. This means:

- **First-party loggers** use `structlog.get_logger()` with keyword-argument context binding (`log.info("event", key=value)`).
- **Third-party stdlib loggers** (e.g. `httpx`, `sqlalchemy`) are automatically picked up by the same handler chain.
- **Console output** uses `ConsoleRenderer` (colourised, human-readable) by default, switching to `JSONRenderer` when `CLI_APP_LOG_USE_JSON_FORMATTER=true`.
- **File output** always writes JSON for structured log analysis.
- `structlog.contextvars.bind_contextvars()` lets you attach fields that appear on every subsequent log line within a request or command invocation.

`setup_logging()` in `utils/log.py` must be called once at startup (`main.py`) before any logger is used. Before it is called (e.g. during tests), structlog is configured to output to stderr via `PrintLoggerFactory` so it never pollutes stdout.

## Output Format Pattern

Commands read `ctx.obj["output_format"]` (set by the root callback) and call `render_output()` from `utils/output.py`:

```python
render_output(
    {"key": value},           # data for JSON mode
    fmt,
    text_render=lambda: console.print(...),   # callable for text mode
)
```

This keeps JSON and human output co-located in the command while staying testable independently.

## Stdin Piping Pattern

`utils/stdin.py` provides `read_stdin_if_piped()` which returns `None` when stdin is a TTY (interactive) and the stdin content when piped. The recommended pattern is:

```python
resolved = argument if argument is not None else read_stdin_if_piped()
if not resolved:
    ...raise Exit(1)
```

This lets commands accept both `cli-app cmd arg` and `echo arg | cli-app cmd`.

Note: `CliRunner` in tests uses a BytesIO stdin whose `isatty()` returns `False`, so `is_stdin_piped()` always returns `True` in tests. Checking `if not resolved:` (rather than `if resolved is None:`) correctly rejects the empty-string case that CliRunner produces when no `input=` is given.

## Commitizen & Versioning

[Commitizen](https://commitizen-tools.github.io/commitizen/) reads Conventional Commit messages to determine the next version and generate CHANGELOG entries. Configuration lives in `[tool.commitizen]` in `pyproject.toml`:

```toml
version_provider = "uv"          # reads/writes the version in pyproject.toml
update_changelog_on_bump = true
major_version_zero = true        # 0.x.y — breaking changes don't force 1.0
```

The `commit-msg` pre-commit hook rejects commits that don't follow the format (`feat:`, `fix:`, `chore:`, etc.).

## Renaming the Template

To use this as a real project:

1. Rename `src/cli_app/` to your package name (e.g. `src/myapp/`)
2. Update `name` in `pyproject.toml`
3. Update `module-name` in `[tool.uv.build-backend]` to match the new directory name
4. Update the console script entry point under `[project.scripts]`
5. Update `[tool.coverage.run]` source, `[tool.ruff.lint.isort]` known-local-folder
6. Update env-var prefixes (`CLI_APP_*`) in `ConsoleConfig`, `LogConfig`, and `Settings`
7. Do a global find-and-replace of `cli_app.` imports to your new package name

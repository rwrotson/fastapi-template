# Getting Started

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Installation

```bash
git clone <repo-url>
cd typer-template
uv sync --all-extras
uv run pre-commit install
```

## Running the CLI

```bash
uv run cli-app --help
uv run cli-app --version
uv run cli-app --authors
```

### Global flags

These flags work in front of any subcommand:

```bash
# Enable DEBUG logging for the duration of the command
uv run cli-app --verbose command example-command hello

# Emit machine-readable JSON instead of Rich text
uv run cli-app --output-format json command example-command hello

# Pipe stdin into a command
echo "hello" | uv run cli-app command example-command
```

### Shell completion

```bash
# Install completion for the current shell
uv run cli-app completion install

# Or target a specific shell
uv run cli-app completion install --shell zsh

# Print the script without installing
uv run cli-app completion show
```

## Development Commands

Tasks are available via taskipy — run with `uv run task <name>`:

```bash
uv run task lint        # ruff check .
uv run task fmt         # ruff format .
uv run task typecheck   # mypy src/
uv run task test        # pytest (parallel, 80% coverage enforced)
uv run task test-fast   # pytest --no-cov -n auto
uv run task audit       # pip-audit dependency audit
```

Or run the tools directly:

```bash
uv run pytest                        # full suite
uv run pytest --no-cov               # skip coverage (faster)
uv run pytest tests/path/to/test.py  # single file
```

## Versioning & Changelog

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) — enforced by the `commit-msg` pre-commit hook.

```bash
uv run cz bump            # bump version, update CHANGELOG, create tag
uv run cz changelog       # update CHANGELOG without bumping
uv run cz changelog --dry-run
```

Bump type is inferred from commits: `fix:` → patch · `feat:` → minor · `feat!:` / `BREAKING CHANGE:` → major.

## Adding a Command Group

1. Create `src/cli_app/cli/commands/my_command.py`:

```python
import structlog
from typer import Context, Typer

from cli_app.utils.console import get_console
from cli_app.utils.output import OutputFormat, render_output

app = Typer()
console = get_console()
log = structlog.get_logger()


@app.command()
def my_action(ctx: Context, name: str) -> None:
    """Do something."""
    log.debug("my_action called", name=name)
    fmt = ctx.obj.get("output_format", OutputFormat.text) if ctx.obj else OutputFormat.text
    render_output(
        {"name": name},
        fmt,
        text_render=lambda: console.print(f"Hello, [bold]{name}[/bold]!"),
    )
```

2. Export it from `src/cli_app/cli/commands/__init__.py`:

```python
from .my_command import app as my_command_app
```

3. Register it in `src/cli_app/cli/app.py`:

```python
from cli_app.cli.commands import my_command_app
app.add_typer(my_command_app, name="my-command")
```

### Stdin support

Use `read_stdin_if_piped()` to accept piped input as a fallback when an argument is omitted:

```python
from cli_app.utils.stdin import read_stdin_if_piped

@app.command()
def process(ctx: Context, text: str | None = None) -> None:
    resolved = text if text is not None else read_stdin_if_piped()
    if not resolved:
        raise typer.Exit(1)
    ...
```

## Configuration

Behaviour can be overridden via environment variables or a `.env` file:

| Prefix | Controls |
|--------|----------|
| `CLI_APP_CONSOLE_*` | Rich console (theme, colors, width) |
| `CLI_APP_LOG_*` | Log level, file path, rotation, JSON format |

```env
CLI_APP_LOG_LEVEL=DEBUG
CLI_APP_LOG_USE_JSON_FORMATTER=true   # JSON logs for Datadog/Loki/etc.
CLI_APP_CONSOLE_WIDTH=120
```

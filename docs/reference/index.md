# API Reference

Auto-generated from source docstrings. Each page corresponds to a module in `src/`.

| Module | Purpose |
|--------|---------|
| `src.main` | Entry point — wires logging, console, and CLI app |
| `src.cli.app` | Root Typer app; registers subcommand groups and eager options |
| `src.cli.callbacks.meta` | Eager callbacks for `--version` and `--authors` |
| `src.cli.commands.command` | Example command group |
| `src.cli.commands.meta` | Meta command group |
| `src.utils.console` | Singleton Rich `Console` with theming |
| `src.utils.log` | File + console logging with rotation; optional JSON output |
| `src.utils.meta` | Reads distribution metadata at runtime |
| `src.utils.format` | Rich `Theme` with `info`/`warning`/`danger` styles |
| `src.utils.emoji` | `Emoji` StrEnum for consistent emoji usage |
| `src.utils.progress` | Rich `Progress` bar wired to the project console |
| `src.utils.misc` | `find_project_root()` helper |

import json
from collections.abc import Callable
from enum import StrEnum
from typing import Any

import typer

from cli_app.utils.console import get_console


class OutputFormat(StrEnum):
    """Output format for CLI commands."""

    text = "text"
    json = "json"


def echo_json(data: dict[str, Any] | list[Any]) -> None:
    """Serialise *data* to JSON and write it to stdout."""
    typer.echo(json.dumps(data, indent=2, default=str))


def render_output(
    data: dict[str, Any] | list[Any],
    fmt: OutputFormat,
    *,
    text_render: Callable[[], None] | None = None,
) -> None:
    """Render *data* in the requested format.

    When *fmt* is ``OutputFormat.json`` the data is serialised to JSON.
    When *fmt* is ``OutputFormat.text`` *text_render* is called if provided;
    otherwise the data is printed via the Rich console.
    """
    if fmt == OutputFormat.json:
        echo_json(data)
    elif text_render is not None:
        text_render()
    else:
        get_console().print(data)

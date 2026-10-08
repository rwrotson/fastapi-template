from typing import Annotated

import structlog
import typer
from typer import Argument, Context, Option, Typer

from cli_app.utils.console import get_console
from cli_app.utils.output import OutputFormat, render_output
from cli_app.utils.stdin import read_stdin_if_piped

app = Typer()
console = get_console()
log = structlog.get_logger()


@app.command()
def example_command(
    ctx: Context,
    argument: Annotated[
        str | None,
        Argument(
            help="Input value. Omit to read from stdin when piped.",
        ),
    ] = None,
    option: Annotated[
        int | None,
        Option(
            "-o",
            "--option",
            "--opt",
            help="Help text for integer option.",
        ),
    ] = None,
) -> None:
    """Help text for command example."""
    resolved = argument if argument is not None else read_stdin_if_piped()
    if not resolved:
        console.print("[danger]Error: argument required (or pipe input via stdin).[/danger]")
        raise typer.Exit(1)

    log.debug("example_command invoked", argument=resolved, option=option)

    fmt = ctx.obj.get("output_format", OutputFormat.text) if ctx.obj else OutputFormat.text
    render_output(
        {"argument": resolved, "option": option},
        fmt,
        text_render=lambda: console.print(f"argument=[bold]{resolved}[/bold] option={option}"),
    )

from cli_app.cli.app import app
from cli_app.utils.console import get_console
from cli_app.utils.log import setup_logging


def main() -> None:
    setup_logging()
    get_console()
    app()

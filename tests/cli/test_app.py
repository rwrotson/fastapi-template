import json

import pytest
from typer.testing import CliRunner

from cli_app.cli.app import app

runner = CliRunner()


def test_version_output_contains_app_name() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "cli-app" in result.output


@pytest.mark.parametrize("flag", ["--authors", "-A"])
def test_authors_flag_shows_author_name(flag: str) -> None:
    result = runner.invoke(app, [flag])
    assert result.exit_code == 0
    assert "Igor Lashkov" in result.output


def test_example_command_with_argument_exits_zero() -> None:
    result = runner.invoke(app, ["command", "example-command", "hello"])
    assert result.exit_code == 0


def test_example_command_missing_argument_fails() -> None:
    result = runner.invoke(app, ["command", "example-command"])
    assert result.exit_code != 0


def test_example_command_with_integer_option() -> None:
    result = runner.invoke(app, ["command", "example-command", "hello", "--option", "42"])
    assert result.exit_code == 0


@pytest.mark.parametrize("flag", ["--verbose", "-V"])
def test_verbose_flag_exits_zero(flag: str) -> None:
    result = runner.invoke(app, [flag, "command", "example-command", "hello"])
    assert result.exit_code == 0


def test_output_format_json_produces_valid_json() -> None:
    result = runner.invoke(app, ["--output-format", "json", "command", "example-command", "hello"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["argument"] == "hello"
    assert data["option"] is None


def test_output_format_json_includes_option_value() -> None:
    result = runner.invoke(
        app, ["--output-format", "json", "command", "example-command", "hello", "--option", "7"]
    )
    assert result.exit_code == 0
    assert json.loads(result.output)["option"] == 7  # noqa: PLR2004


def test_output_format_text_is_default() -> None:
    result = runner.invoke(app, ["command", "example-command", "hello"])
    assert result.exit_code == 0
    assert "hello" in result.output


def test_output_format_invalid_value_fails() -> None:
    result = runner.invoke(app, ["--output-format", "xml", "command", "example-command", "hi"])
    assert result.exit_code != 0

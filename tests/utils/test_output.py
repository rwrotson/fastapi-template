import json

import pytest

from cli_app.utils.output import OutputFormat, echo_json, render_output


def test_output_format_values() -> None:
    assert OutputFormat.text == "text"
    assert OutputFormat.json == "json"


def test_echo_json_produces_valid_json(capsys: pytest.CaptureFixture[str]) -> None:
    echo_json({"key": "value", "num": 42})
    data = json.loads(capsys.readouterr().out)
    assert data == {"key": "value", "num": 42}


def test_echo_json_list(capsys: pytest.CaptureFixture[str]) -> None:
    echo_json([1, 2, 3])
    assert json.loads(capsys.readouterr().out) == [1, 2, 3]


def test_render_output_json(capsys: pytest.CaptureFixture[str]) -> None:
    render_output({"a": 1}, OutputFormat.json)
    assert json.loads(capsys.readouterr().out) == {"a": 1}


def test_render_output_text_calls_render() -> None:
    called: list[bool] = []
    render_output({"a": 1}, OutputFormat.text, text_render=lambda: called.append(True))
    assert called == [True]

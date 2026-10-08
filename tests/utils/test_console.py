import pytest
from rich.console import Console

from cli_app.utils.console import ConsoleConfig, get_console

_DEFAULT_TAB_SIZE = 8
_CONSOLE_WIDTH = 120


def test_console_config_defaults() -> None:
    config = ConsoleConfig()
    assert config.markup is True
    assert config.emoji is True
    assert config.highlight is True
    assert config.safe_box is True
    assert config.record is False
    assert config.tab_size == _DEFAULT_TAB_SIZE
    assert config.color_system == "auto"
    assert config.log_time is True
    assert config.log_path is True


def test_get_console_returns_console_instance() -> None:
    assert isinstance(get_console(), Console)


def test_get_console_is_cached() -> None:
    assert get_console() is get_console()


def test_console_config_env_var_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLI_APP_CONSOLE_WIDTH", str(_CONSOLE_WIDTH))
    config = ConsoleConfig()
    assert config.width == _CONSOLE_WIDTH

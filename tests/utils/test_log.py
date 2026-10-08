import logging
import logging.handlers
from pathlib import Path

import pytest
from pydantic import ValidationError

from cli_app.utils.log import LogConfig, setup_logging

_FILE_BACKUP_COUNT = 5
_LOG_DIR_MAX_BYTES = 4 * 1024 * 1024
_EXPECTED_HANDLER_COUNT = 2


def test_log_config_defaults() -> None:
    config = LogConfig()
    assert config.level == logging.INFO
    assert config.console_level == logging.DEBUG
    assert config.file_level == logging.INFO
    assert config.use_json_formatter is False
    assert config.file_name == "cli-app.log"
    assert config.file_max_bytes == _LOG_DIR_MAX_BYTES
    assert config.file_backup_count == _FILE_BACKUP_COUNT


def test_log_config_level_from_string() -> None:
    config = LogConfig(level="DEBUG")  # type: ignore[arg-type]
    assert config.level == logging.DEBUG


def test_log_config_level_from_int() -> None:
    config = LogConfig(level=logging.WARNING)
    assert config.level == logging.WARNING


def test_log_config_console_level_from_string() -> None:
    config = LogConfig(console_level="WARNING")  # type: ignore[arg-type]
    assert config.console_level == logging.WARNING


def test_log_config_invalid_level_raises() -> None:
    with pytest.raises(ValidationError):
        LogConfig(level="NOTLEVEL")  # type: ignore[arg-type]


def test_log_config_level_from_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLI_APP_LOG_LEVEL", "WARNING")
    config = LogConfig()
    assert config.level == logging.WARNING


def test_setup_logging_creates_log_dir(tmp_path: Path, clean_root_logger: logging.Logger) -> None:
    _ = clean_root_logger
    log_dir = tmp_path / "logs"
    config = LogConfig(dir=log_dir)
    setup_logging(config)
    assert log_dir.exists()


def test_setup_logging_does_not_add_duplicate_handlers(
    tmp_path: Path, clean_root_logger: logging.Logger
) -> None:
    config = LogConfig(dir=tmp_path / "logs2")
    setup_logging(config)
    count_after_first = len(clean_root_logger.handlers)
    setup_logging(config)
    assert len(clean_root_logger.handlers) == count_after_first


def test_setup_logging_sets_root_level(tmp_path: Path, clean_root_logger: logging.Logger) -> None:
    config = LogConfig(dir=tmp_path / "logs3", level=logging.WARNING)
    setup_logging(config)
    assert clean_root_logger.level == config.level


def test_setup_logging_adds_two_handlers(tmp_path: Path, clean_root_logger: logging.Logger) -> None:
    config = LogConfig(dir=tmp_path / "logs4")
    setup_logging(config)
    app_handlers = [
        h
        for h in clean_root_logger.handlers
        if type(h) in {logging.handlers.RotatingFileHandler, logging.StreamHandler}
    ]
    assert len(app_handlers) == _EXPECTED_HANDLER_COUNT


def test_setup_logging_json_formatter(tmp_path: Path, clean_root_logger: logging.Logger) -> None:
    _ = clean_root_logger
    config = LogConfig(dir=tmp_path / "logs5", use_json_formatter=True)
    setup_logging(config)  # should not raise
    assert True

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from functools import cache, partial
from typing import IO, Final, Literal, cast

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console, HighlighterType
from rich.highlighter import ReprHighlighter
from rich.style import Style
from rich.text import Text
from rich.theme import Theme

from cli_app.utils.format import get_theme

_CONSOLE_CONFIG_DYNAMIC_FIELDS_MAPPING: Final[dict[str, dict[str, Callable[..., object]]]] = {
    "log_time_format": {},
    "highlighter": {
        "ReprHighlighter": ReprHighlighter(),
    },
    "get_datetime": {
        "now": partial(datetime.now, tz=UTC),
    },
    "get_time": {
        "now": lambda: datetime.now(tz=UTC).timestamp(),
    },
}


class ConsoleConfig(BaseSettings):
    """Pydantic settings for the Rich console, configurable via CLI_APP_CONSOLE_* env vars."""

    color_system: Literal["auto", "standard", "256", "truecolor", "windows"] | None = "auto"
    force_terminal: bool | None = None
    force_jupyter: bool | None = None
    force_interactive: bool | None = None
    soft_wrap: bool | None = None
    theme: Theme | None = get_theme()
    stderr: bool | None = None
    file: IO[str] | None = None
    quiet: bool | None = None
    width: int | None = None
    height: int | None = None
    style: Style | str | None = None
    no_color: bool | None = None
    tab_size: int | None = 8
    record: bool | None = False
    markup: bool | None = True
    emoji: bool | None = True
    emoji_variant: Literal["emoji", "text"] | None = None
    highlight: bool | None = True
    log_time: bool | None = True
    log_path: bool | None = True
    log_time_format: str | Callable[[datetime], Text] = "[%X]"
    highlighter: HighlighterType | None = ReprHighlighter()
    legacy_windows: bool | None = None
    safe_box: bool | None = True
    get_datetime: Callable[[], datetime] | None = None
    get_time: Callable[[], float] | None = None
    _environ: Mapping[str, str] | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CLI_APP_CONSOLE_",
        extra="ignore",
        case_sensitive=False,
        arbitrary_types_allowed=True,
    )

    @field_validator("log_time_format", "highlighter", "get_datetime", "get_time", mode="before")
    @classmethod
    def _provide_with_callables[T](cls, v: T | str, info: ValidationInfo) -> T | str:
        if isinstance(v, str) and info.field_name:
            field_mapping = _CONSOLE_CONFIG_DYNAMIC_FIELDS_MAPPING.get(info.field_name, {})
            return cast(T | str, field_mapping.get(v) or v)
        return v


@cache
def get_console() -> Console:
    return Console(**ConsoleConfig().model_dump())

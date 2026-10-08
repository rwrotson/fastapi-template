from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. Add fields here; configure via CLI_APP_* env vars or .env."""

    model_config = SettingsConfigDict(
        env_prefix="CLI_APP_",
        env_file=".env",
        extra="ignore",
    )

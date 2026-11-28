# Config

- `src/app/config/settings.py` defines `Settings` (Pydantic Settings): defaults in code, `APP_*` environment variables, and `.env`. Nested models use `__` (`APP_REDIS__DSN`).
- Storage settings are optional nested models; a backend is enabled when its DSN (or ClickHouse host) is set. Secrets are `SecretStr`.
- Every field needs a `description`; the docs configuration page is generated from `Settings` (do not edit the generated page).
- Every setting must appear in `.env.example`; a test enforces it. Also update README, `docs/`, and `compose.yml` when a setting is public or affects deployment.
- `create_app()` owns one settings instance and lifespan binds it through a FastAPI dependency provider. Do not read the environment elsewhere or keep module-level mutable settings.
- `app.config` imports nothing from the other application packages; import-linter enforces it.
- A setting that holds a credential is a `SecretStr` and gets step-by-step instructions in a README "Credentials" section in the same change.
- Ruff `banned-api` bans `os.environ`, `os.getenv` and `os.putenv` outside `src/app/config/` and `tests/`.

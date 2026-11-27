# Tests

- `tests/` mirrors the layers: `services/`, `api/`, `infra/`, `core/`, `config/`, plus `contracts/` and `integration/`.
- Tests run in random order (pytest-randomly); warnings are errors and each test has a 30-second timeout. `poe test` enforces 95% branch coverage. Reproduce an order-dependent failure with `uv run pytest -p randomly --randomly-seed=<seed>`.
- Shared fakes live in `tests/fakes.py` and shared fixtures in `tests/conftest.py`. Autouse fixtures remove `APP_*` variables, run each test in a temporary working directory (so a local `.env` is not read), and restore logging and structlog configuration.
- Use the `fake_backends` fixture to stub storage clients; use `app`, `client`, and `settings` for HTTP tests.
- Behaviour that every port adapter must share belongs in `tests/contracts/`. Run it against the fake in unit tests and against the real backend in `tests/integration/`; contract subclasses provide a `unit_of_work_factory` fixture whose instances share storage.
- Tests never use the network, except `tests/integration/`. Those tests are marked `integration`, skip without `APP_POSTGRES_ORM__DSN`, and fail when selected with `-m integration` and no DSN. Run them with `uv run poe test-integration` against a migrated database.
- For endpoint changes, test status codes, response schemas, problem details, and behavior when an optional backend is absent.
- Test use-case behavior without FastAPI or a database; test the HTTP mapping separately.
- Test functions and fixtures need type annotations (mypy strict covers `tests/`) but no docstrings.
- Run a focused file or `-k` selection before the full suite.

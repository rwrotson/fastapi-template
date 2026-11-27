# Tests

- `tests/` mirrors the layers: `services/`, `api/`, `infra/`, `core/`, `config/`, plus `contracts/` and `integration/`.
- Tests run in parallel (pytest-xdist) and in random order (pytest-randomly); warnings are errors and each test has a 30-second timeout. `poe test` enforces 95% branch coverage. Reproduce an order-dependent failure with `uv run pytest -p randomly --randomly-seed=<seed>`.
- Shared fakes live in `tests/fakes.py` and shared fixtures in `tests/conftest.py`. Autouse fixtures remove `APP_*` variables, run each test in a temporary working directory (so a local `.env` is not read), and restore logging and structlog configuration.
- `tests/test_package.py` imports `app` and `app.main` in fresh interpreters and checks that import reads no `.env`, configures no logging, and loads no optional storage drivers. A test requires a `description` on every setting.
- Use the `fake_backends` fixture to stub storage clients; use `app`, `client`, and `settings` for HTTP tests.
- Behaviour that every port adapter must share belongs in `tests/contracts/`. Run it against the fake in unit tests and against the real backend in `tests/integration/`; contract subclasses provide a `unit_of_work_factory` fixture whose instances share storage.
- Tests never use the network: pytest-socket disables sockets (Unix sockets stay allowed for xdist). Only `tests/integration/` may use it, with `pytestmark = pytest.mark.enable_socket`.
- `tests/integration/` is collected only with `--live` (`tests/conftest.py`), so `poe test` and `poe check` skip it. With `--live` and no `APP_POSTGRES_ORM__DSN`, `tests/integration/conftest.py` raises `pytest.UsageError`. Run it with `uv run poe test-live` against a migrated database (serial, fixed order, reads an optional `.env`).
- When tests need an external program, check for it once in `pytest_configure` and raise `pytest.UsageError` with one clear message.
- For endpoint changes, test status codes, response schemas, problem details, and behavior when an optional backend is absent.
- Test use-case behavior without FastAPI or a database; test the HTTP mapping separately.
- Test functions and fixtures need type annotations (mypy strict covers `tests/`) but no docstrings.
- Run a focused file or `-k` selection before the full suite.

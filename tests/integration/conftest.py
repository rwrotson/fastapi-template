import os

import pytest

DSN_VARIABLE = "APP_POSTGRES_ORM__DSN"


def pytest_configure(config: pytest.Config) -> None:
    if config.getoption("--live") and not os.environ.get(DSN_VARIABLE):
        raise pytest.UsageError(f"{DSN_VARIABLE} is required to run integration tests")


@pytest.fixture(scope="session")
def postgres_dsn() -> str:
    """Capture the integration DSN before the test fixture clears APP_* variables."""
    return os.environ[DSN_VARIABLE]

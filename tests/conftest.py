import logging
from collections.abc import Generator

import pytest


@pytest.fixture
def clean_root_logger() -> Generator[logging.Logger]:
    root = logging.getLogger()
    original_handlers, original_level = root.handlers[:], root.level
    root.handlers = []
    yield root
    for h in root.handlers:
        h.close()
    root.handlers = original_handlers
    root.setLevel(original_level)

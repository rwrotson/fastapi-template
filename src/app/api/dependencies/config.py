from typing import Annotated

from fastapi import Depends

from app.api.dependencies.container import get_container
from app.config import Settings
from app.container import AppContainer


def get_config(container: Annotated[AppContainer, Depends(get_container)]) -> Settings:
    """Return settings bound to the current FastAPI application."""
    return container.settings

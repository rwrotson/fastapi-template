from fastapi import Request

from app.container import AppContainer


def get_container(request: Request) -> AppContainer:
    """Return the container that lifespan placed in the request state."""
    container = getattr(request.state, "container", None)
    if not isinstance(container, AppContainer):
        raise RuntimeError("Application container is not initialized")
    return container

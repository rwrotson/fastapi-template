from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.dependencies.storage import Storage

router = APIRouter(tags=["health"])


@router.get("/live")
async def live() -> dict[str, str]:
    """Report that the HTTP process is alive."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(storage: Storage) -> JSONResponse:
    """Return 503 while any configured backend is unavailable."""
    dependencies = await storage.readiness()
    available = all(status == "ok" for status in dependencies.values())
    return JSONResponse(
        status_code=200 if available else 503,
        content={"status": "ok" if available else "unavailable", "dependencies": dependencies},
    )

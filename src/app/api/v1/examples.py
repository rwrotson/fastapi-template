import structlog
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.greeting import greeting_message

router = APIRouter(prefix="/examples", tags=["examples"])


class Greeting(BaseModel):
    """Example response schema."""

    name: str
    message: str


class TaskRequest(BaseModel):
    """Example request accepted for an in-process background task."""

    message: str = Field(min_length=1, max_length=200)


class TaskAccepted(BaseModel):
    """A task was queued in the current application process."""

    status: str = "accepted"


def log_example_task(message: str) -> None:
    """Demonstrate a short local background task without external services."""
    structlog.get_logger().info("example_task", message=message)


@router.post("/tasks", status_code=202)
async def submit_task(payload: TaskRequest, background_tasks: BackgroundTasks) -> TaskAccepted:
    """Queue a brief in-process log task."""
    background_tasks.add_task(log_example_task, payload.message)
    return TaskAccepted()


@router.get("/{name}")
async def greet(name: str) -> Greeting:
    """Demonstrate a typed API response."""
    return Greeting(name=name, message=greeting_message(name))

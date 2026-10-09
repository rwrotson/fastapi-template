from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

import structlog
from pydantic import BaseModel
from starlette.responses import JSONResponse

PROBLEM_MEDIA_TYPE = "application/problem+json"


class Problem(BaseModel):
    """RFC 9457 problem details returned for every error response."""

    type: str = "about:blank"
    title: str
    status: int
    detail: Any = None
    instance: str | None = None
    request_id: str | None = None
    errors: list[dict[str, Any]] | None = None


def problem_response(
    status: int,
    *,
    detail: object = None,
    instance: str | None = None,
    errors: list[dict[str, Any]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """Build a problem response that carries the current request ID."""
    request_id = structlog.contextvars.get_contextvars().get("request_id")
    problem = Problem(
        title=HTTPStatus(status).phrase,
        status=status,
        detail=detail,
        instance=instance,
        request_id=request_id,
        errors=errors,
    )
    return JSONResponse(
        problem.model_dump(mode="json", exclude_none=True),
        status_code=status,
        headers=headers,
        media_type=PROBLEM_MEDIA_TYPE,
    )

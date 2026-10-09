from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import Response

from app.core.problems import PROBLEM_MEDIA_TYPE, Problem, problem_response
from app.services.errors import ConflictError, NotFoundError


def problem_responses(*statuses: int) -> dict[int | str, dict[str, Any]]:
    """Document error statuses as problem details in OpenAPI."""
    content = {PROBLEM_MEDIA_TYPE: {"schema": {"$ref": "#/components/schemas/Problem"}}}
    return {
        status: {"model": Problem, "description": HTTPStatus(status).phrase, "content": content}
        for status in statuses
    }


PROBLEM_RESPONSES = problem_responses(422, 500, 503)


async def http_error(request: Request, exc: Exception) -> Response:
    """Render an HTTP exception as a problem response."""
    assert isinstance(exc, HTTPException)
    return problem_response(
        exc.status_code, detail=exc.detail, instance=request.url.path, headers=exc.headers
    )


async def validation_error(request: Request, exc: Exception) -> Response:
    """Render request validation failures as problem responses."""
    assert isinstance(exc, RequestValidationError)
    return problem_response(
        422,
        detail="Request validation failed",
        instance=request.url.path,
        errors=jsonable_encoder(exc.errors()),
    )


async def not_found(request: Request, exc: Exception) -> Response:
    """Render a missing resource as a problem response."""
    return problem_response(404, detail=str(exc), instance=request.url.path)


async def conflict(request: Request, exc: Exception) -> Response:
    """Render a service conflict as a problem response."""
    return problem_response(409, detail=str(exc), instance=request.url.path)


def register_error_handlers(application: FastAPI) -> None:
    """Render HTTP, validation and use-case errors as RFC 9457 problem details."""
    application.add_exception_handler(HTTPException, http_error)
    application.add_exception_handler(RequestValidationError, validation_error)
    application.add_exception_handler(NotFoundError, not_found)
    application.add_exception_handler(ConflictError, conflict)

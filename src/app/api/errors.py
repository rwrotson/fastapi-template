from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import Response

from app.core.problems import PROBLEM_MEDIA_TYPE, Problem, problem_response
from app.services.errors import ConflictError, NotFoundError, ServiceError


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
    if not isinstance(exc, HTTPException):
        raise TypeError("Expected HTTPException")
    return problem_response(
        exc.status_code,
        detail=exc.detail,
        instance=request.url.path,
        headers=exc.headers,
    )


async def validation_error(request: Request, exc: Exception) -> Response:
    """Render request validation failures as problem responses."""
    if not isinstance(exc, RequestValidationError):
        raise TypeError("Expected RequestValidationError")
    return problem_response(
        422,
        detail="Request validation failed",
        instance=request.url.path,
        errors=jsonable_encoder(exc.errors()),
    )


ERROR_STATUS: dict[type[ServiceError], int] = {
    NotFoundError: 404,
    ConflictError: 409,
}


def status_for_error(exc: ServiceError) -> int:
    """Resolve the HTTP status of a service error from the nearest mapped base class."""
    for cls in type(exc).__mro__:
        if cls in ERROR_STATUS:
            return ERROR_STATUS[cls]
    return 500


async def service_error(request: Request, exc: Exception) -> Response:
    """Render a service error as a problem response."""
    if not isinstance(exc, ServiceError):
        raise TypeError("Expected ServiceError")
    return problem_response(status_for_error(exc), detail=str(exc), instance=request.url.path)


def register_error_handlers(application: FastAPI) -> None:
    """Render HTTP, validation and use-case errors as RFC 9457 problem details."""
    application.add_exception_handler(HTTPException, http_error)
    application.add_exception_handler(RequestValidationError, validation_error)
    for error_type in ERROR_STATUS:
        application.add_exception_handler(error_type, service_error)

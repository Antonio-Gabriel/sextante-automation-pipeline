"""Opaque, Portuguese error responses with a correlation id (REQ-PLT-005, SEC-15)."""

import logging
from collections.abc import Mapping
from typing import Final

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from sextante.platform.errors import DomainError
from sextante.platform.structured_logging import correlation_id_var
from sextante.platform.user_messages import USER_MESSAGES_PT

logger = logging.getLogger(__name__)

DOMAIN_ERROR_DEFAULT_STATUS: Final = 422


class ErrorResponse(BaseModel):
    """Body of every refused or failed request: stable code, Portuguese message, reference."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    correlation_id: str


# Declared on the application so the OpenAPI document, and the frontend's generated
# types, carry the error body of every route.
ERROR_RESPONSES: Final[dict[int | str, dict[str, object]]] = {
    "4XX": {"model": ErrorResponse, "description": "Refused, with the Portuguese message."},
    "5XX": {"model": ErrorResponse, "description": "Failed, with a reference for support."},
}


def error_response(
    status_code: int, user_message_key: str, headers: Mapping[str, str] | None = None
) -> JSONResponse:
    """Build the error body: stable code, Portuguese message, correlation id.

    Example:
        return error_response(404, "errors.job.not_found")
    """
    return JSONResponse(
        status_code=status_code,
        headers=dict(headers or {}),
        content=ErrorResponse(
            code=user_message_key,
            message=USER_MESSAGES_PT[user_message_key],
            correlation_id=correlation_id_var.get(),
        ).model_dump(),
    )


def install_error_handlers(app: FastAPI, status_by_error: Mapping[type[DomainError], int]) -> None:
    """Answer domain errors with their Portuguese message, unexpected ones with an opaque 500.

    The HTTP status of a domain error is looked up by its class, so the domain never
    knows about HTTP; an unlisted domain error answers 422.

    Example:
        install_error_handlers(app, {JobNotFoundError: 404})
    """

    @app.exception_handler(DomainError)
    async def respond_to_domain_error(request: Request, error: DomainError) -> JSONResponse:
        status = next(
            (code for error_type, code in status_by_error.items() if isinstance(error, error_type)),
            DOMAIN_ERROR_DEFAULT_STATUS,
        )
        return error_response(status, error.user_message_key, error.response_headers())

    @app.exception_handler(Exception)
    async def respond_to_unexpected_error(request: Request, error: Exception) -> JSONResponse:
        logger.error("unhandled_error", extra={"error_type": type(error).__name__})
        return error_response(500, DomainError.user_message_key)

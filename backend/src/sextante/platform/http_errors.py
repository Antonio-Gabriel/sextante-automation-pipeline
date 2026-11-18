"""Opaque, Portuguese error responses with a correlation id (REQ-PLT-005, SEC-15)."""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from sextante.platform.errors import DomainError
from sextante.platform.structured_logging import correlation_id_var
from sextante.platform.user_messages import USER_MESSAGES_PT

logger = logging.getLogger(__name__)


def error_response(status_code: int, user_message_key: str) -> JSONResponse:
    """Build the error body: stable code, Portuguese message, correlation id.

    Example:
        return error_response(404, "errors.job.not_found")
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "code": user_message_key,
            "message": USER_MESSAGES_PT[user_message_key],
            "correlation_id": correlation_id_var.get(),
        },
    )


def install_error_handlers(app: FastAPI) -> None:
    """Answer unexpected errors with an opaque 500 and keep the detail in the server log.

    Example:
        install_error_handlers(app)
    """

    @app.exception_handler(Exception)
    async def respond_to_unexpected_error(request: Request, error: Exception) -> JSONResponse:
        logger.error("unhandled_error", extra={"error_type": type(error).__name__})
        return error_response(500, DomainError.user_message_key)

"""Opaque error responses, in the request's language, with a correlation id (REQ-PLT-005)."""

import logging
from collections.abc import Mapping
from typing import Final

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.exceptions import HTTPException as StarletteHTTPException

from sextante.platform.errors import DomainError
from sextante.platform.language import Language
from sextante.platform.request_language import request_language
from sextante.platform.structured_logging import correlation_id_var
from sextante.platform.user_messages import user_message

logger = logging.getLogger(__name__)

DOMAIN_ERROR_DEFAULT_STATUS: Final = 422
# The framework's own refusals, before any route runs, in the same error body.
FRAMEWORK_ERROR_KEYS: Final[Mapping[int, str]] = {
    404: "errors.request.not_found",
    405: "errors.request.method_not_allowed",
}
INVALID_REQUEST_KEY: Final = "errors.request.invalid"


class ErrorResponse(BaseModel):
    """Body of every refused or failed request: stable code, message, reference."""

    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    correlation_id: str


# Declared on the application so the OpenAPI document, and the frontend's generated
# types, carry the error body of every route.
ERROR_RESPONSES: Final[dict[int | str, dict[str, object]]] = {
    "4XX": {
        "model": ErrorResponse,
        "description": "Refused, with the message in the request's language.",
    },
    "5XX": {"model": ErrorResponse, "description": "Failed, with a reference for support."},
}


def error_response(
    status_code: int,
    user_message_key: str,
    language: Language,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """Build the error body: stable code, message in the language, correlation id.

    Example:
        return error_response(404, "errors.job.not_found", Language.PT)
    """
    return JSONResponse(
        status_code=status_code,
        headers=dict(headers or {}),
        content=ErrorResponse(
            code=user_message_key,
            message=user_message(user_message_key, language),
            correlation_id=correlation_id_var.get(),
        ).model_dump(),
    )


def install_error_handlers(app: FastAPI, status_by_error: Mapping[type[DomainError], int]) -> None:
    """Answer every refusal and failure with the same body, in the request's language.

    Domain errors carry their message; the framework's own refusals (an invalid request,
    an unknown address or method) get a generic one, never the framework's English
    detail; unexpected errors an opaque 500. The HTTP status of a domain error is looked
    up by its class, so the domain never knows about HTTP; an unlisted one answers 422.

    Example:
        install_error_handlers(app, {JobNotFoundError: 404})
    """
    _install_domain_handlers(app, status_by_error)
    _install_framework_handlers(app)


def _install_domain_handlers(
    app: FastAPI, status_by_error: Mapping[type[DomainError], int]
) -> None:
    @app.exception_handler(DomainError)
    async def respond_to_domain_error(request: Request, error: DomainError) -> JSONResponse:
        status = next(
            (code for error_type, code in status_by_error.items() if isinstance(error, error_type)),
            DOMAIN_ERROR_DEFAULT_STATUS,
        )
        language = request_language(request)
        return error_response(status, error.user_message_key, language, error.response_headers())

    @app.exception_handler(Exception)
    async def respond_to_unexpected_error(request: Request, error: Exception) -> JSONResponse:
        logger.error("unhandled_error", extra={"error_type": type(error).__name__})
        return error_response(500, DomainError.user_message_key, request_language(request))


def _install_framework_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def respond_to_invalid_request(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        # The detail names fields and echoes input: it stays out of the answer (SEC-15).
        return error_response(422, INVALID_REQUEST_KEY, request_language(request))

    @app.exception_handler(StarletteHTTPException)
    async def respond_to_framework_refusal(
        request: Request, error: StarletteHTTPException
    ) -> JSONResponse:
        key = FRAMEWORK_ERROR_KEYS.get(error.status_code, INVALID_REQUEST_KEY)
        headers = dict(error.headers or {})
        return error_response(error.status_code, key, request_language(request), headers)

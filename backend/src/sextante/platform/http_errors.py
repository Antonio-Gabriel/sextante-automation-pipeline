"""Opaque error responses, in the request's language, with a correlation id (REQ-PLT-005)."""

import logging
from collections.abc import Mapping
from typing import Final

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from sextante.platform.errors import DomainError
from sextante.platform.language import DEFAULT_LANGUAGE, Language, parse_accept_language
from sextante.platform.structured_logging import correlation_id_var
from sextante.platform.user_messages import user_message

logger = logging.getLogger(__name__)

DOMAIN_ERROR_DEFAULT_STATUS: Final = 422


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
    headers: Mapping[str, str] | None = None,
    language: Language = DEFAULT_LANGUAGE,
) -> JSONResponse:
    """Build the error body: stable code, message in the language, correlation id.

    Example:
        return error_response(404, "errors.job.not_found", language=Language.PT)
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
    """Answer domain errors with their message, unexpected ones with an opaque 500, each in
    the language the request asks (Accept-Language).

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
        language = _language_of(request)
        return error_response(status, error.user_message_key, error.response_headers(), language)

    @app.exception_handler(Exception)
    async def respond_to_unexpected_error(request: Request, error: Exception) -> JSONResponse:
        logger.error("unhandled_error", extra={"error_type": type(error).__name__})
        return error_response(500, DomainError.user_message_key, language=_language_of(request))


def _language_of(request: Request) -> Language:
    return parse_accept_language(request.headers.get("accept-language"))

"""The language a request asks its texts in, from its Accept-Language header."""

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, FastAPI, Request, Response

from sextante.platform.language import Language, parse_accept_language


def request_language(request: Request) -> Language:
    """The request's language; English when the header names no supported one.

    Example:
        language = request_language(request)
    """
    return parse_accept_language(request.headers.get("accept-language"))


RequestLanguage = Annotated[Language, Depends(request_language)]


def install_vary_on_language(app: FastAPI) -> None:
    """Say on every answer that it depends on Accept-Language, so no cache mixes languages.

    Example:
        install_vary_on_language(app)
    """

    @app.middleware("http")
    async def vary_on_language(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers.append("Vary", "Accept-Language")
        return response

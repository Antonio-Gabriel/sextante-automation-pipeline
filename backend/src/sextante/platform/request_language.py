"""The language a request asks its texts in, from its Accept-Language header."""

from typing import Annotated

from fastapi import Depends, Request

from sextante.platform.language import Language, parse_accept_language


def request_language(request: Request) -> Language:
    """The request's language; English when the header names no supported one.

    Example:
        language = request_language(request)
    """
    return parse_accept_language(request.headers.get("accept-language"))


RequestLanguage = Annotated[Language, Depends(request_language)]

"""Correlation id per HTTP request (NFR-OBS-001, REQ-PLT-005)."""

import uuid
from typing import Final

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from sextante.platform.structured_logging import correlation_id_var

CORRELATION_HEADER: Final = "X-Correlation-ID"


class CorrelationIdMiddleware:
    """Give every HTTP request a fresh correlation id, in the logs and in the response.

    A plain ASGI middleware, so the id is set in the same context in which the server
    writes its access line and the application writes its records.

    Example:
        app.add_middleware(CorrelationIdMiddleware)
    """

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Run the request with its own correlation id and return the id as a header."""
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        correlation_id = uuid.uuid4().hex
        token = correlation_id_var.set(correlation_id)

        async def send_with_header(message: Message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)[CORRELATION_HEADER] = correlation_id
            await send(message)

        try:
            await self._app(scope, receive, send_with_header)
        finally:
            correlation_id_var.reset(token)

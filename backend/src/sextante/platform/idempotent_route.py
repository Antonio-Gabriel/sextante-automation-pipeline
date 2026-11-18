"""Run a POST or PATCH handler once per Idempotency-Key (SEC-19)."""

from typing import Annotated

from fastapi import Depends, Header, Request, Response

from sextante.platform.idempotency import (
    IdempotentExecutor,
    JsonBody,
    Operation,
    body_fingerprint,
    require_key,
)

IDEMPOTENCY_HEADER = "Idempotency-Key"


async def run_idempotently(
    request: Request, response: Response, body: JsonBody, operation: Operation
) -> JsonBody:
    """Run the operation, or replay the answer stored for this key, scope and body.

    The status code of the answer, run or replayed, is set on ``response``.

    The scope is the reviewer, the method and the path, so one key never reaches another
    resource; the body's fingerprint tells a repeat from a reuse.

    Example:
        answer = await run_idempotently(request, response, body.model_dump(), operation)

    Raises:
        IdempotencyKeyRequiredError: when the header is missing or malformed.
        IdempotencyKeyReusedError: when the key was used with another body.
    """
    key = require_key(request.headers.get(IDEMPOTENCY_HEADER))
    executor: IdempotentExecutor = request.app.state.idempotency
    scope = f"{request.app.state.reviewer_id}:{request.method}:{request.url.path}"
    status, answer = await executor.run(scope, key, body_fingerprint(body), operation)
    response.status_code = status
    return answer


def _declare_idempotency_key(
    idempotency_key: Annotated[
        str | None,
        Header(
            alias=IDEMPOTENCY_HEADER,
            description=(
                "Mandatory. A key you choose for this request, 1 to 128 characters of letters, "
                "digits, '.', '_', ':' or '-'. Sending the same request again with the same key "
                "returns the same answer and acts once (SEC-19)."
            ),
        ),
    ] = None,
) -> None:
    # Declares the header in the API description, so clients and the interactive docs
    # can send it; run_idempotently is what validates and uses it.
    return None


# Add to a route's dependencies to declare Idempotency-Key in its API description.
IDEMPOTENCY_KEY_DECLARED = Depends(_declare_idempotency_key)

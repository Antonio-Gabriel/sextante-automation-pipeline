"""Run a POST or PATCH handler once per Idempotency-Key (SEC-19)."""

from fastapi import Request

from sextante.platform.idempotency import (
    IdempotentExecutor,
    JsonBody,
    Operation,
    body_fingerprint,
    require_key,
)

IDEMPOTENCY_HEADER = "Idempotency-Key"


async def run_idempotently(request: Request, body: JsonBody, operation: Operation) -> JsonBody:
    """Run the operation, or replay the answer stored for this key, scope and body.

    The scope is the reviewer, the method and the path, so one key never reaches another
    resource; the body's fingerprint tells a repeat from a reuse.

    Example:
        answer = await run_idempotently(request, body.model_dump(), operation)

    Raises:
        IdempotencyKeyRequiredError: when the header is missing or malformed.
        IdempotencyKeyReusedError: when the key was used with another body.
    """
    key = require_key(request.headers.get(IDEMPOTENCY_HEADER))
    executor: IdempotentExecutor = request.app.state.idempotency
    scope = f"{request.app.state.reviewer_id}:{request.method}:{request.url.path}"
    _, answer = await executor.run(scope, key, body_fingerprint(body), operation)
    return answer

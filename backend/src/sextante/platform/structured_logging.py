"""JSON logs on stdout with a correlation id and a redaction filter (NFR-OBS-001, SEC-15)."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Final, TextIO

APPLICATION_LOGGER: Final = "sextante"
STARTUP_CORRELATION_ID: Final = "startup"
REDACTED: Final = "[redacted]"

# Fields that carry what fed a decision rather than what explains it (SEC-15). They are
# masked here so that one forgotten extra= does not turn into a leak.
REDACTED_FIELDS: Final = frozenset(
    {
        "description",
        "line_description",
        "supplier_name",
        "billed_entity",
        "amount",
        "unit_price",
        "total",
        "prompt",
        "model_response",
        "api_key",
        "original_filename",
    }
)

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default=STARTUP_CORRELATION_ID)

_STANDARD_RECORD_FIELDS: Final = frozenset(
    vars(logging.LogRecord("", 0, "", 0, "", None, None)).keys() | {"message", "asctime"}
)


class JsonLogFormatter(logging.Formatter):
    """Format a record as one JSON object: event, level, timestamp, correlation id, extras.

    Example:
        handler.setFormatter(JsonLogFormatter())
    """

    def format(self, record: logging.LogRecord) -> str:
        """Render the record as a single JSON line."""
        entry: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
            "logger": record.name,
            "correlation_id": correlation_id_var.get(),
        }
        entry.update(_extra_fields(record))
        return json.dumps(entry, ensure_ascii=False, default=str)


def _extra_fields(record: logging.LogRecord) -> dict[str, object]:
    return {
        key: REDACTED if key in REDACTED_FIELDS else value
        for key, value in vars(record).items()
        if key not in _STANDARD_RECORD_FIELDS
    }


def configure_logging(stream: TextIO | None = None) -> None:
    """Send the application's records to stdout as JSON. Safe to call more than once.

    Example:
        configure_logging()
    """
    logger = logging.getLogger(APPLICATION_LOGGER)
    for existing in list(logger.handlers):
        if isinstance(existing.formatter, JsonLogFormatter):
            logger.removeHandler(existing)
    handler = logging.StreamHandler(stream if stream is not None else sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

"""JSON logs on stdout with a correlation id and a redaction filter (NFR-OBS-001, SEC-15)."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Final, TextIO

APPLICATION_LOGGER: Final = "sextante"
# The server's own loggers, so that startup and access lines are JSON as well.
SERVER_LOGGERS: Final = ("uvicorn", "uvicorn.error", "uvicorn.access")
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

# Standard LogRecord attributes are not extras; color_message is uvicorn's terminal-colour
# copy of the message, display noise in a JSON log.
_NON_EXTRA_FIELDS: Final = frozenset(
    vars(logging.LogRecord("", 0, "", 0, "", None, None)).keys()
    | {"message", "asctime", "color_message"}
)


class JsonLogFormatter(logging.Formatter):
    """Format a record as one JSON object: event, level, timestamp, correlation id, extras.

    Example:
        stream_output.setFormatter(JsonLogFormatter())
    """

    def format(self, record: logging.LogRecord) -> str:
        """Render the record as a single JSON line, with forbidden fields redacted.

        Example:
            JsonLogFormatter().format(record)  # '{"event": "catalog_item_warning", ...}'
        """
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
        if key not in _NON_EXTRA_FIELDS
    }


def configure_logging(stream: TextIO | None = None) -> None:
    """Send application and server records to stdout as JSON. Safe to call more than once.

    Records do not propagate further: the JSON stream is the only place they are written,
    so no other handler can write a record without redaction (SEC-15).

    Example:
        configure_logging()
    """
    for logger_name in (APPLICATION_LOGGER, *SERVER_LOGGERS):
        _route_to_json_stream(logging.getLogger(logger_name), stream or sys.stdout)


def _route_to_json_stream(logger: logging.Logger, stream: TextIO) -> None:
    json_output = logging.StreamHandler(stream)
    json_output.setFormatter(JsonLogFormatter())
    logger.handlers = [json_output]
    logger.propagate = False
    logger.setLevel(logging.INFO)

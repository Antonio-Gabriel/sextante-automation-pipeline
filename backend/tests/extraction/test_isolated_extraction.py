"""Operation ticket 03: PDF extraction in a separate process, with limits (SEC-16).

Tested at the InvoiceExtractor port, with SYNTHETIC hostile PDFs, and once through the
API to show the worker carries on with the other invoices.
"""

import logging
import sys
import time
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from sextante.ingestion.domain.model import ExtractionRejection, FileFormat, RejectionReason
from sextante.ingestion.infrastructure.isolated_extractor import (
    MIB,
    ExtractionLimits,
    IsolatedPdfExtractor,
)
from sextante.ingestion.infrastructure.pdf_invoice_extractor import PdfInvoiceExtractor
from sextante.main import AppDependencies, create_app
from sextante.platform.settings import Settings, StartupConfigurationError
from tests.conftest import SYNTHETIC_API_KEY
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fixtures.synthetic_pdf import (
    air_ticket_pdf,
    decompression_bomb_pdf,
    model_invoice_pdf,
    other_document_pdf,
    scanned_pdf,
    slow_to_read_pdf,
)

MIN_CHARS_PER_PAGE = 100
LIMITS = ExtractionLimits(memory_bytes=512 * MIB, timeout_seconds=30.0)
ISOLATED_LOGGER = "sextante.ingestion.infrastructure.isolated_extractor"
UNSUPPORTED = ExtractionRejection(RejectionReason.UNSUPPORTED_DOCUMENT_TYPE)


def _isolated(limits: ExtractionLimits = LIMITS) -> IsolatedPdfExtractor:
    return IsolatedPdfExtractor(MIN_CHARS_PER_PAGE, limits)


@pytest.fixture
def limit_log(caplog: pytest.LogCaptureFixture) -> Iterator[pytest.LogCaptureFixture]:
    """Capture the extractor's records, whether or not an earlier app stopped propagation."""
    isolated_logger = logging.getLogger(ISOLATED_LOGGER)
    isolated_logger.addHandler(caplog.handler)
    caplog.set_level(logging.WARNING, logger=ISOLATED_LOGGER)
    yield caplog
    isolated_logger.removeHandler(caplog.handler)


def _limit_records(caplog: pytest.LogCaptureFixture) -> list[dict[str, object]]:
    # The same record may reach the capture twice, through the handler and propagation.
    unique = {id(r): r for r in caplog.records if r.msg == "pdf_extraction_limit_reached"}
    return [vars(record) for record in unique.values()]


@pytest.mark.requirement("REQ-ING-003", "SEC-16")
@pytest.mark.parametrize(
    "content",
    [
        model_invoice_pdf(air_ticket_pdf()),
        scanned_pdf(),
        other_document_pdf(),
        b"%PDF-1.4\nnot a readable PDF",
    ],
    ids=["invoice", "scanned", "other_document", "unreadable"],
)
def test_a_pdf_read_apart_gives_what_it_gave_before(content: bytes) -> None:
    """The same extraction, or the same refusal, as reading in the process."""
    expected = PdfInvoiceExtractor(MIN_CHARS_PER_PAGE).extract(content, FileFormat.PDF)

    assert _isolated().extract(content, FileFormat.PDF) == expected


@pytest.mark.requirement("SEC-16", "SEC-15")
@pytest.mark.skipif(sys.platform != "linux", reason="Only Linux enforces RLIMIT_AS (SEC-16).")
def test_a_decompression_bomb_is_refused_as_unsupported_by_the_memory_limit(
    limit_log: pytest.LogCaptureFixture,
) -> None:
    """A 1 MiB file that expands to 1 GiB stops at the limit; the log names the limit only."""
    result = _isolated().extract(decompression_bomb_pdf(), FileFormat.PDF)

    assert result == UNSUPPORTED
    [record] = _limit_records(limit_log)
    assert (record["limit"], record["memory_mib"], record["timeout_seconds"]) == (
        "memory",
        512,
        30.0,
    )


@pytest.mark.requirement("SEC-16", "SEC-15")
def test_a_pdf_that_takes_too_long_is_refused_as_unsupported_by_the_time_limit(
    limit_log: pytest.LogCaptureFixture,
) -> None:
    """Reading stops at the time limit, whatever the file was doing."""
    limits = ExtractionLimits(memory_bytes=LIMITS.memory_bytes, timeout_seconds=1.0)
    started = time.monotonic()

    result = _isolated(limits).extract(slow_to_read_pdf(), FileFormat.PDF)

    assert result == UNSUPPORTED
    assert time.monotonic() - started < 5.0
    [record] = _limit_records(limit_log)
    assert (record["limit"], record["timeout_seconds"]) == ("time", 1.0)


@pytest.mark.requirement("REQ-ING-009")
def test_an_xlsx_is_refused_without_starting_a_process() -> None:
    """XLSX extraction is not implemented (D-3.6): refused as before."""
    assert _isolated().extract(b"PK\x03\x04", FileFormat.XLSX) == UNSUPPORTED


@pytest.mark.requirement("SEC-16", "REQ-PLT-002")
@pytest.mark.skipif(sys.platform != "linux", reason="Only Linux enforces RLIMIT_AS (SEC-16).")
def test_the_worker_carries_on_after_a_hostile_pdf(valid_environment: dict[str, str]) -> None:
    """The bomb is refused with its reason; the next invoice of the job is coded."""
    files = [
        ("files", ("bomb.pdf", decompression_bomb_pdf(), "application/pdf")),
        ("files", ("ticket.pdf", model_invoice_pdf(air_ticket_pdf()), "application/pdf")),
    ]
    app = create_app(valid_environment, AppDependencies(classifier=FakeItemClassifier()))
    with TestClient(app, headers={"X-API-Key": SYNTHETIC_API_KEY}) as client:
        job_id = client.post("/api/invoices", files=files).json()["job_id"]
        job = _finished(client, job_id)

    assert job["invoice_counts"] == {"rejected": 1, "encoded": 1}


@pytest.mark.requirement("SEC-16")
def test_the_default_limits_are_declared(valid_environment: dict[str, str]) -> None:
    """Without overrides: 512 MiB and 30 seconds per PDF."""
    settings = Settings.from_environment(valid_environment)

    assert (settings.pdf_extraction_memory_mib, settings.pdf_extraction_timeout_seconds) == (
        512,
        30,
    )


@pytest.mark.requirement("SEC-16")
@pytest.mark.parametrize(
    ("setting", "value"),
    [
        ("SEXTANTE_PDF_EXTRACTION_MEMORY_MIB", "64"),
        ("SEXTANTE_PDF_EXTRACTION_TIMEOUT_SECONDS", "0"),
    ],
)
def test_a_limit_out_of_range_refuses_startup(
    valid_environment: dict[str, str], setting: str, value: str
) -> None:
    """Too little memory would refuse every PDF; no time limit would hold the worker."""
    with pytest.raises(StartupConfigurationError, match=setting):
        create_app({**valid_environment, setting: value})


def _finished(client: TestClient, job_id: str) -> dict[str, object]:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        job: dict[str, object] = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in {"completed", "failed"}:
            return job
        time.sleep(0.05)
    raise AssertionError(f"Job {job_id} did not finish")

"""Operation ticket 02: a ceiling on model calls per window, in the worker (SEC-12)."""

import asyncio
import json
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from fastapi.testclient import TestClient

from sextante.ingestion.contracts import ExtractedInvoice
from sextante.main import AppDependencies, create_app, model_call_ceiling
from sextante.matching.contracts import ItemClassifierUnavailableError
from sextante.platform.settings import Settings, StartupConfigurationError
from tests.conftest import SYNTHETIC_API_KEY
from tests.fakes.fake_invoice_extractor import FakeInvoiceExtractor
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fakes.fixed_clock import FixedClock, SequentialIdentifierGenerator
from tests.fixtures.synthetic_invoices import SyntheticInvoice, hotel_stay_to_amt

POLL_SECONDS = 0.01
TIMEOUT_SECONDS = 5.0
# Retry backoffs are seconds; a ceiling wait is part of a window, here of an hour.
HELD_SLEEP_SECONDS = 60.0


class _HeldClock:
    """A monotonic clock that moves only when the worker sleeps, and only once released.

    A wait for the ceiling blocks until the test calls ``release``; then the clock moves
    by the seconds asked, as if they had passed. A retry's short backoff passes at once.
    """

    def __init__(self) -> None:
        self.seconds = 1000.0
        self.sleeps: list[float] = []
        self._released = threading.Event()

    def __call__(self) -> float:
        return self.seconds

    def release(self) -> None:
        self._released.set()

    async def sleep(self, seconds: float) -> None:
        if seconds < HELD_SLEEP_SECONDS:
            return
        self.sleeps.append(seconds)
        while not self._released.is_set():
            await asyncio.sleep(POLL_SECONDS)
        self.seconds += seconds


@contextmanager
def _application(
    environment: dict[str, str],
    invoices: list[SyntheticInvoice],
    classifier: FakeItemClassifier,
    clock: _HeldClock,
    ceiling: int,
) -> Iterator[TestClient]:
    dependencies = AppDependencies(
        extractor=FakeInvoiceExtractor(invoices),
        classifier=classifier,
        clock=FixedClock(),
        identifiers=SequentialIdentifierGenerator(),
        worker_poll_seconds=POLL_SECONDS,
        sleep=clock.sleep,
        monotonic=clock,
    )
    environment = {**environment, "SEXTANTE_MODEL_CALL_CEILING": str(ceiling)}
    with TestClient(
        create_app(environment, dependencies), headers={"X-API-Key": SYNTHETIC_API_KEY}
    ) as client:
        yield client


def _invoices(count: int) -> list[SyntheticInvoice]:
    base = hotel_stay_to_amt()
    return [
        SyntheticInvoice(
            file_name=f"ceiling-{n}.pdf",
            content=base.content + f"-{n}".encode(),
            extraction=base.extraction,
        )
        for n in range(count)
    ]


def _upload(client: TestClient, invoices: list[SyntheticInvoice]) -> str:
    files = [("files", (i.file_name, i.content, "application/pdf")) for i in invoices]
    response = client.post("/api/invoices", files=files)
    assert response.status_code == 202, response.text
    return str(response.json()["job_id"])


def _wait_for_status(client: TestClient, job_id: str, statuses: set[str]) -> dict[str, Any]:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        job: dict[str, Any] = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in statuses:
            return job
        time.sleep(POLL_SECONDS)
    raise AssertionError(f"Job {job_id} never reached {statuses}")


@pytest.mark.requirement("SEC-12", "REQ-PLT-002")
def test_over_the_ceiling_invoices_wait_queued_and_are_coded_when_the_window_opens(
    valid_environment: dict[str, str],
) -> None:
    """The ceiling delays work and never loses it: no invoice fails because of it."""
    classifier = FakeItemClassifier({1: "O00004", 2: "O00051"})
    clock = _HeldClock()
    with _application(valid_environment, _invoices(3), classifier, clock, ceiling=2) as client:
        job_id = _upload(client, _invoices(3))
        waiting = _wait_for_status(client, job_id, {"waiting_model"})
        clock.release()
        finished = _wait_for_status(client, job_id, {"completed", "failed"})

    assert waiting["invoice_counts"] == {"encoded": 2, "queued": 1}
    assert finished["status"] == "completed"
    assert finished["invoice_counts"] == {"encoded": 3}
    assert len(classifier.calls) == 3
    # The stopwatch reads 1000 s: the hour window ends at 3600 s, 2600 s away.
    assert clock.sleeps == [2600.0]


@pytest.mark.requirement("SEC-12", "REQ-PLT-003")
def test_every_attempt_counts_against_the_ceiling(valid_environment: dict[str, str]) -> None:
    """A retry is a paid call too: one invoice retried once uses two calls of the ceiling."""
    unavailable = ItemClassifierUnavailableError("Model call failed. Expected an answer.")
    classifier = FakeItemClassifier({1: "O00004", 2: "O00051"}, failures=[unavailable])
    clock = _HeldClock()
    with _application(valid_environment, _invoices(2), classifier, clock, ceiling=2) as client:
        job_id = _upload(client, _invoices(2))
        waiting = _wait_for_status(client, job_id, {"waiting_model"})
        clock.release()
        finished = _wait_for_status(client, job_id, {"completed", "failed"})

    assert waiting["invoice_counts"] == {"encoded": 1, "queued": 1}
    assert finished["invoice_counts"] == {"encoded": 2}


@pytest.mark.requirement("SEC-12", "SEC-15")
def test_the_log_says_when_the_ceiling_delays_work_without_invoice_content(
    valid_environment: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    """The job and the wait are logged; no supplier, description or amount."""
    clock = _HeldClock()
    classifier = FakeItemClassifier({1: "O00004", 2: "O00051"})
    with _application(valid_environment, _invoices(2), classifier, clock, ceiling=1) as client:
        job_id = _upload(client, _invoices(2))
        _wait_for_status(client, job_id, {"waiting_model"})
        clock.release()
        _wait_for_status(client, job_id, {"completed", "failed"})

    records = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line]
    [delayed] = [r for r in records if r.get("event") == "model_call_ceiling_reached"]
    assert delayed["job_id"] == job_id
    assert delayed["wait_seconds"] == 2600.0
    text = json.dumps(delayed)
    extraction = hotel_stay_to_amt().extraction
    assert isinstance(extraction, ExtractedInvoice)
    assert extraction.supplier.name
    assert extraction.supplier.name not in text
    assert all(line.description not in text for line in extraction.lines)


@pytest.mark.requirement("SEC-12")
def test_the_default_ceiling_is_declared(valid_environment: dict[str, str]) -> None:
    """Without overrides: 200 model calls per hour."""
    ceiling = model_call_ceiling(Settings.from_environment(valid_environment))

    assert (ceiling.requests, ceiling.window_seconds) == (200, 3600.0)


@pytest.mark.requirement("SEC-12")
@pytest.mark.parametrize(
    "setting", ["SEXTANTE_MODEL_CALL_CEILING", "SEXTANTE_MODEL_CALL_WINDOW_SECONDS"]
)
def test_a_ceiling_or_window_below_one_refuses_startup(
    valid_environment: dict[str, str], setting: str
) -> None:
    """A ceiling of zero would stop all coding by accident; it is refused, named."""
    with pytest.raises(StartupConfigurationError, match=setting):
        create_app({**valid_environment, setting: "0"})

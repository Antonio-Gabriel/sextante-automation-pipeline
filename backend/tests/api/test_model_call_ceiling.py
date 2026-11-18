"""Operation ticket 02: a ceiling on model calls per window, in the worker (SEC-12)."""

import json
import time
from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from sextante.ingestion.contracts import ExtractedInvoice
from sextante.main import AppDependencies, create_app, model_call_limit
from sextante.matching.contracts import ItemClassifierUnavailableError
from sextante.platform.settings import Settings, StartupConfigurationError
from tests.conftest import SYNTHETIC_API_KEY
from tests.fakes.fake_invoice_extractor import FakeInvoiceExtractor
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fakes.fixed_clock import FixedClock, SequentialIdentifierGenerator
from tests.fakes.held_clock import POLL_SECONDS, HeldClock
from tests.fixtures.synthetic_invoices import (
    SyntheticInvoice,
    hotel_stay_to_amt,
    scanned_pdf_without_text,
)

TIMEOUT_SECONDS = 5.0
FINISHED = frozenset({"completed", "failed"})

Job = dict[str, object]


@contextmanager
def _application(
    environment: dict[str, str],
    invoices: list[SyntheticInvoice],
    classifier: FakeItemClassifier,
    clock: HeldClock,
    ceiling: int,
    first_identifier: int = 0,
) -> Iterator[TestClient]:
    dependencies = AppDependencies(
        extractor=FakeInvoiceExtractor(invoices),
        classifier=classifier,
        clock=FixedClock(),
        identifiers=SequentialIdentifierGenerator(first_identifier),
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
        SyntheticInvoice(f"ceiling-{n}.pdf", base.content + f"-{n}".encode(), base.extraction)
        for n in range(count)
    ]


def _classifier(failures: int = 0) -> FakeItemClassifier:
    unavailable = ItemClassifierUnavailableError("Model call failed. Expected an answer.")
    return FakeItemClassifier({1: "O00004", 2: "O00051"}, failures=[unavailable] * failures)


def _upload(client: TestClient, invoices: list[SyntheticInvoice]) -> str:
    files = [("files", (i.file_name, i.content, "application/pdf")) for i in invoices]
    response = client.post("/api/invoices", files=files)
    assert response.status_code == 202, response.text
    return str(response.json()["job_id"])


def _wait_for_status(client: TestClient, job_id: str, statuses: frozenset[str]) -> Job:
    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        job: Job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in statuses:
            return job
        time.sleep(POLL_SECONDS)
    raise AssertionError(f"Job {job_id} never reached {set(statuses)}")


def _waiting(client: TestClient, job_id: str) -> Job:
    return _wait_for_status(client, job_id, frozenset({"waiting_model"}))


@pytest.mark.requirement("SEC-12", "REQ-PLT-002")
def test_over_the_ceiling_invoices_wait_queued_and_are_coded_when_the_window_opens(
    valid_environment: dict[str, str],
) -> None:
    """The ceiling delays work and never loses it: no invoice fails because of it."""
    classifier, clock = _classifier(), HeldClock()
    with _application(valid_environment, _invoices(3), classifier, clock, ceiling=2) as client:
        job_id = _upload(client, _invoices(3))
        waiting = _waiting(client, job_id)
        clock.release()
        finished = _wait_for_status(client, job_id, FINISHED)

    assert waiting["invoice_counts"] == {"encoded": 2, "queued": 1}
    assert (finished["status"], finished["invoice_counts"]) == ("completed", {"encoded": 3})
    assert len(classifier.calls) == 3
    # The clock reads 1000 s: the hour window ends at 3600 s, 2600 s away.
    assert clock.sleeps == [2600.0]


@pytest.mark.requirement("SEC-12", "REQ-PLT-003")
def test_a_retry_over_the_ceiling_waits_and_the_job_shows_it(
    valid_environment: dict[str, str],
) -> None:
    """A retry is a paid call too: with a ceiling of one, the retry waits for the window."""
    classifier, clock = _classifier(failures=1), HeldClock()
    with _application(valid_environment, _invoices(1), classifier, clock, ceiling=1) as client:
        job_id = _upload(client, _invoices(1))
        waiting = _waiting(client, job_id)
        clock.release()
        finished = _wait_for_status(client, job_id, FINISHED)

    assert waiting["invoice_counts"] == {"queued": 1}
    assert finished["invoice_counts"] == {"encoded": 1}
    assert len(classifier.calls) == 2


@pytest.mark.requirement("SEC-12", "REQ-ING-002")
def test_an_invoice_without_a_model_call_never_waits_for_the_ceiling(
    valid_environment: dict[str, str],
) -> None:
    """A refused document uses no call, so a full ceiling does not hold it."""
    invoices = [*_invoices(1), scanned_pdf_without_text()]
    classifier, clock = _classifier(), HeldClock()
    with _application(valid_environment, invoices, classifier, clock, ceiling=1) as client:
        job_id = _upload(client, invoices)
        finished = _wait_for_status(client, job_id, FINISHED)

    assert finished["invoice_counts"] == {"encoded": 1, "rejected": 1}
    assert clock.sleeps == []


@pytest.mark.requirement("SEC-12", "NFR-REL-002")
def test_an_invoice_reprocessed_while_its_job_waits_is_coded_again(
    valid_environment: dict[str, str],
) -> None:
    """The reprocessing queues the job again; the worker keeps it queued and claims it again."""
    classifier, clock = _classifier(), HeldClock()
    with _application(valid_environment, _invoices(2), classifier, clock, ceiling=1) as client:
        job_id = _upload(client, _invoices(2))
        _waiting(client, job_id)
        lines = client.get(f"/api/jobs/{job_id}/results").json()["lines"]
        reprocess = client.post(
            f"/api/invoices/{lines[0]['invoice_id']}/reprocess",
            headers={"Idempotency-Key": "while-waiting"},
        )
        clock.release()
        finished = _wait_for_status(client, job_id, FINISHED)

    assert reprocess.status_code == 202, reprocess.text
    assert finished["invoice_counts"] == {"encoded": 2}
    assert len(classifier.calls) == 3


@pytest.mark.requirement("SEC-12", "NFR-REL-001")
def test_a_job_left_waiting_by_a_stopped_process_is_coded_after_restart(
    valid_environment: dict[str, str],
) -> None:
    """A stop during the wait loses nothing: at startup the job is queued again."""
    invoices = _invoices(2)
    with _application(valid_environment, invoices, _classifier(), HeldClock(), 1) as client:
        job_id = _upload(client, invoices)
        _waiting(client, job_id)

    restarted = HeldClock(released=True)
    with _application(
        valid_environment, invoices, _classifier(), restarted, 1, first_identifier=1000
    ) as client:
        finished = _wait_for_status(client, job_id, FINISHED)

    assert (finished["status"], finished["invoice_counts"]) == ("completed", {"encoded": 2})


@pytest.mark.requirement("SEC-12", "SEC-15")
def test_the_log_says_when_the_ceiling_delays_work_without_invoice_content(
    valid_environment: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    """The job and the wait are logged; no supplier, description or amount."""
    clock = HeldClock()
    with _application(valid_environment, _invoices(2), _classifier(), clock, ceiling=1) as client:
        job_id = _upload(client, _invoices(2))
        _waiting(client, job_id)
        clock.release()
        _wait_for_status(client, job_id, FINISHED)

    records = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line]
    [delayed] = [r for r in records if r.get("event") == "model_call_ceiling_reached"]
    assert (delayed["job_id"], delayed["wait_seconds"]) == (job_id, 2600.0)
    text = json.dumps(delayed)
    extraction = hotel_stay_to_amt().extraction
    assert isinstance(extraction, ExtractedInvoice)
    assert extraction.supplier.name
    assert extraction.supplier.name not in text
    assert all(line.description not in text for line in extraction.lines)


@pytest.mark.requirement("SEC-12")
def test_the_default_ceiling_is_declared(valid_environment: dict[str, str]) -> None:
    """Without overrides: 200 model calls per hour."""
    limit = model_call_limit(Settings.from_environment(valid_environment))

    assert (limit.requests, limit.window_seconds) == (200, 3600.0)


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

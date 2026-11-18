"""Build the application with test doubles and drive it like an HTTP client."""

import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Final

from fastapi.testclient import TestClient

from sextante.main import AppDependencies, create_app
from tests.fakes.fake_invoice_extractor import FakeInvoiceExtractor
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fakes.fixed_clock import FixedClock, SequentialIdentifierGenerator
from tests.fixtures.synthetic_invoices import SyntheticInvoice

WORKER_POLL_SECONDS: Final = 0.01
JOB_TIMEOUT_SECONDS: Final = 5.0
FINISHED_JOB_STATUSES: Final = frozenset({"completed", "failed"})


@dataclass
class EncodingHarness:
    """A running application with its doubles, for API tests."""

    client: TestClient
    extractor: FakeInvoiceExtractor
    classifier: FakeItemClassifier

    def upload(self, *invoices: SyntheticInvoice) -> dict[str, object]:
        """Upload the invoices in one request and return the response body."""
        files = [("files", (i.file_name, i.content, "application/pdf")) for i in invoices]
        response = self.client.post("/api/invoices", files=files)
        assert response.status_code == 202, response.text
        body: dict[str, object] = response.json()
        return body

    def wait_for_job(self, job_id: object) -> dict[str, object]:
        """Poll the job until the worker finishes it, and return its final state."""
        deadline = time.monotonic() + JOB_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            job: dict[str, object] = self.client.get(f"/api/jobs/{job_id}").json()
            if job["status"] in FINISHED_JOB_STATUSES:
                return job
            time.sleep(WORKER_POLL_SECONDS)
        raise AssertionError(f"Job {job_id} did not finish within {JOB_TIMEOUT_SECONDS}s")

    def results(self, job_id: object, **params: int) -> dict[str, object]:
        """Return one page of the job's encoded lines."""
        response = self.client.get(f"/api/jobs/{job_id}/results", params=params)
        assert response.status_code == 200, response.text
        body: dict[str, object] = response.json()
        return body


@contextmanager
def running_application(
    environment: dict[str, str],
    invoices: list[SyntheticInvoice],
    classifier: FakeItemClassifier,
) -> Iterator[EncodingHarness]:
    """Start the application with fakes for the extractor and the model, nothing else.

    Example:
        with running_application(env, [invoice], FakeItemClassifier({1: "O00004"})) as app:
            app.upload(invoice)
    """
    extractor = FakeInvoiceExtractor(invoices)
    dependencies = AppDependencies(
        extractor=extractor,
        classifier=classifier,
        clock=FixedClock(),
        identifiers=SequentialIdentifierGenerator(),
        worker_poll_seconds=WORKER_POLL_SECONDS,
    )
    with TestClient(create_app(environment, dependencies)) as client:
        yield EncodingHarness(client=client, extractor=extractor, classifier=classifier)

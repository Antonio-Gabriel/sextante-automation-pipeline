"""Operation ticket 01: rate limits per endpoint, with 429 and Retry-After (SEC-12, SEC-19)."""

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from sextante.main import AppDependencies, create_app
from tests.conftest import SYNTHETIC_API_KEY
from tests.fakes.fake_item_classifier import FakeItemClassifier
from tests.fakes.fixed_clock import FixedClock, SequentialIdentifierGenerator
from tests.fixtures.synthetic_invoices import synthetic_pdf_bytes

KEY = {"X-API-Key": SYNTHETIC_API_KEY}


class _Stopwatch:
    """A monotonic clock the test moves by hand."""

    def __init__(self) -> None:
        self.seconds = 1000.0

    def __call__(self) -> float:
        return self.seconds


@contextmanager
def _application(
    environment: dict[str, str], stopwatch: _Stopwatch, **limits: str
) -> Iterator[TestClient]:
    dependencies = AppDependencies(
        classifier=FakeItemClassifier(),
        clock=FixedClock(),
        identifiers=SequentialIdentifierGenerator(),
        worker_poll_seconds=3600,
        monotonic=stopwatch,
    )
    with TestClient(create_app({**environment, **limits}, dependencies)) as client:
        yield client


def _upload(client: TestClient, label: str) -> int:
    files = {"files": (f"{label}.pdf", synthetic_pdf_bytes(label), "application/pdf")}
    return client.post("/api/invoices", files=files, headers=KEY).status_code


@pytest.mark.requirement("SEC-12", "SEC-19")
def test_an_endpoint_over_its_limit_answers_429_with_retry_after(
    valid_environment: dict[str, str],
) -> None:
    """The upload allows its quota per minute; the next one waits, with the time to wait."""
    with _application(
        valid_environment, _Stopwatch(), SEXTANTE_RATE_LIMIT_UPLOAD_PER_MINUTE="2"
    ) as client:
        statuses = [_upload(client, f"rate-{n}") for n in range(2)]
        files = {"files": ("rate-3.pdf", synthetic_pdf_bytes("rate-3"), "application/pdf")}
        refused = client.post("/api/invoices", files=files, headers=KEY)

    assert statuses == [202, 202]
    assert refused.status_code == 429
    assert refused.json()["code"] == "errors.rate_limit.exceeded"
    assert 1 <= int(refused.headers["Retry-After"]) <= 60


@pytest.mark.requirement("SEC-12")
def test_the_limit_opens_again_when_its_window_passes(valid_environment: dict[str, str]) -> None:
    """A refused caller who waits the Retry-After is let through."""
    stopwatch = _Stopwatch()
    with _application(
        valid_environment, stopwatch, SEXTANTE_RATE_LIMIT_UPLOAD_PER_MINUTE="1"
    ) as client:
        first = _upload(client, "window-1")
        second = _upload(client, "window-2")
        stopwatch.seconds += 60
        third = _upload(client, "window-3")

    assert (first, second, third) == (202, 429, 202)


@pytest.mark.requirement("SEC-12")
def test_the_general_limit_covers_every_api_call(valid_environment: dict[str, str]) -> None:
    """Reads count too: the general quota is per caller, whatever the endpoint."""
    with _application(
        valid_environment, _Stopwatch(), SEXTANTE_RATE_LIMIT_GENERAL_PER_MINUTE="3"
    ) as client:
        statuses = [client.get("/api/jobs/unknown", headers=KEY).status_code for _ in range(4)]

    assert statuses == [404, 404, 404, 429]


@pytest.mark.requirement("SEC-12", "SEC-06")
def test_health_and_refused_credentials_never_use_the_quota(
    valid_environment: dict[str, str],
) -> None:
    """A monitor polls health freely, and a caller without the key gets 401, not 429."""
    with _application(
        valid_environment, _Stopwatch(), SEXTANTE_RATE_LIMIT_GENERAL_PER_MINUTE="1"
    ) as client:
        health = [client.get("/api/health").status_code for _ in range(5)]
        anonymous = [client.get("/api/jobs/unknown").status_code for _ in range(3)]
        keyed = client.get("/api/jobs/unknown", headers=KEY).status_code

    assert set(health) == {200}
    assert set(anonymous) == {401}
    assert keyed == 404


@pytest.mark.requirement("SEC-12")
def test_each_costly_endpoint_has_its_own_limit(valid_environment: dict[str, str]) -> None:
    """Reprocessing, export and correction are counted apart from the general quota."""
    limits = {
        "SEXTANTE_RATE_LIMIT_REPROCESS_PER_HOUR": "1",
        "SEXTANTE_RATE_LIMIT_EXPORT_PER_HOUR": "1",
        "SEXTANTE_RATE_LIMIT_CORRECTION_PER_MINUTE": "1",
    }
    with _application(valid_environment, _Stopwatch(), **limits) as client:
        reprocess = [
            client.post(
                "/api/invoices/unknown/reprocess",
                headers={**KEY, "Idempotency-Key": f"r-{n}"},
            ).status_code
            for n in range(2)
        ]
        export = [
            client.get("/api/exports/unknown", params={"format": "csv"}, headers=KEY).status_code
            for _ in range(2)
        ]
        correction = [
            client.patch(
                "/api/encoded-lines/unknown",
                json={"item_number": "O00004"},
                headers={**KEY, "Idempotency-Key": f"c-{n}"},
            ).status_code
            for n in range(2)
        ]

    assert (reprocess, export, correction) == ([404, 429], [404, 429], [404, 429])


@pytest.mark.requirement("SEC-12")
def test_a_limit_below_one_refuses_startup(valid_environment: dict[str, str]) -> None:
    """A limit of zero would close the endpoint by accident; it is refused, named."""
    with pytest.raises(Exception, match="SEXTANTE_RATE_LIMIT_UPLOAD_PER_MINUTE"):
        create_app({**valid_environment, "SEXTANTE_RATE_LIMIT_UPLOAD_PER_MINUTE": "0"})


@pytest.mark.requirement("SEC-12")
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known limitation, by design of this version (SEC-12): the counter lives in each "
        "process's memory, so two instances each allow the full quota. A shared counter "
        "(Redis or Valkey) is the production fix, 00-decisoes-e-lacunas.md §6."
    ),
)
def test_two_instances_share_one_quota(valid_environment: dict[str, str]) -> None:
    """Documented as failing: proves the limitation instead of assuming it away."""
    limit = {"SEXTANTE_RATE_LIMIT_GENERAL_PER_MINUTE": "1"}
    with (
        _application(valid_environment, _Stopwatch(), **limit) as first,
        _application(valid_environment, _Stopwatch(), **limit) as second,
    ):
        first.get("/api/jobs/unknown", headers=KEY)
        across = second.get("/api/jobs/unknown", headers=KEY).status_code

    assert across == 429

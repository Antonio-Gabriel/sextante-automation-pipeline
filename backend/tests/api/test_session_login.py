"""Frontend ticket 01: login by access token, opening an HttpOnly session (SEC-06, L-07)."""

from collections.abc import Iterator
from contextlib import contextmanager
from http.cookies import SimpleCookie

import pytest
from fastapi.testclient import TestClient

from sextante.main import AppDependencies, create_app
from sextante.platform.settings import StartupConfigurationError
from tests.conftest import SYNTHETIC_ACCESS_TOKEN, SYNTHETIC_API_KEY

SESSION_COOKIE = "sextante_session"
# The session cookie is Secure by default, so the client speaks HTTPS to the test server.
BASE_URL = "https://testserver"


class _Stopwatch:
    """A monotonic clock the test moves by hand."""

    def __init__(self) -> None:
        self.seconds = 1000.0

    def __call__(self) -> float:
        return self.seconds


@contextmanager
def _client(
    environment: dict[str, str], stopwatch: _Stopwatch | None = None
) -> Iterator[TestClient]:
    dependencies = AppDependencies(monotonic=stopwatch or _Stopwatch(), worker_poll_seconds=3600)
    with TestClient(create_app(environment, dependencies), base_url=BASE_URL) as client:
        yield client


def _login(client: TestClient, token: str = SYNTHETIC_ACCESS_TOKEN) -> int:
    return client.post("/api/session", json={"token": token}).status_code


def _session_cookie(set_cookie: str) -> dict[str, str | bool]:
    morsel = SimpleCookie(set_cookie)[SESSION_COOKIE]
    return {name: morsel[name] for name in ("httponly", "samesite", "secure", "path", "max-age")}


@pytest.mark.requirement("SEC-06", "L-07")
def test_the_right_token_opens_a_session_the_browser_cannot_read(
    valid_environment: dict[str, str],
) -> None:
    """The session lives in an HttpOnly, SameSite=Strict, Secure cookie of limited life."""
    with _client(valid_environment) as client:
        response = client.post("/api/session", json={"token": SYNTHETIC_ACCESS_TOKEN})

    assert response.status_code == 204
    assert _session_cookie(response.headers["set-cookie"]) == {
        "httponly": True,
        "samesite": "strict",
        "secure": True,
        "path": "/api",
        "max-age": str(8 * 3600),
    }


@pytest.mark.requirement("SEC-06", "L-07")
def test_the_session_opens_the_api_without_the_key(valid_environment: dict[str, str]) -> None:
    """After login the browser calls the API with the cookie alone."""
    with _client(valid_environment) as client:
        before = client.get("/api/session").status_code
        _login(client)
        session = client.get("/api/session")
        job = client.get("/api/jobs/unknown").status_code

    assert before == 401
    assert (session.status_code, session.json()) == (200, {"authenticated": True})
    assert job == 404


@pytest.mark.requirement("SEC-06", "L-07")
@pytest.mark.parametrize("token", ["wrong-token-of-enough-length", ""])
def test_a_wrong_token_is_refused_and_opens_nothing(
    valid_environment: dict[str, str], token: str
) -> None:
    """401 with the usual error body, and no cookie."""
    with _client(valid_environment) as client:
        response = client.post("/api/session", json={"token": token})
        after = client.get("/api/session").status_code

    assert response.status_code == 401
    assert response.json()["code"] == "errors.auth.access_token_invalid"
    assert "set-cookie" not in response.headers
    assert after == 401


@pytest.mark.requirement("SEC-06")
def test_the_api_key_is_not_an_access_token(valid_environment: dict[str, str]) -> None:
    """The key of programs and the token of people are two credentials, not one."""
    with _client(valid_environment) as client:
        status = _login(client, SYNTHETIC_API_KEY)

    assert status == 401


@pytest.mark.requirement("SEC-06", "L-07")
def test_logging_out_ends_the_session(valid_environment: dict[str, str]) -> None:
    """The cookie is cleared and the session refused, even if the old cookie is replayed."""
    with _client(valid_environment) as client:
        _login(client)
        old_cookie = client.cookies.get(SESSION_COOKIE)
        assert old_cookie
        logout = client.post("/api/session/end")
        after = client.get("/api/session").status_code
        client.cookies.set(SESSION_COOKIE, old_cookie)
        replayed = client.get("/api/session").status_code

    assert logout.status_code == 204
    assert 'sextante_session=""' in logout.headers["set-cookie"]
    assert (after, replayed) == (401, 401)


@pytest.mark.requirement("SEC-06")
def test_a_session_expires_after_its_validity(valid_environment: dict[str, str]) -> None:
    """Eight hours by default: one second later the session is refused."""
    stopwatch = _Stopwatch()
    with _client(valid_environment, stopwatch) as client:
        _login(client)
        stopwatch.seconds += 8 * 3600 - 1
        inside = client.get("/api/session").status_code
        stopwatch.seconds += 1
        expired = client.get("/api/session").status_code

    assert (inside, expired) == (200, 401)


@pytest.mark.requirement("SEC-06", "SEC-12")
def test_login_attempts_are_limited(valid_environment: dict[str, str]) -> None:
    """Guessing the token is slowed: over the login limit, 429 even for the right token."""
    environment = {**valid_environment, "SEXTANTE_RATE_LIMIT_LOGIN_PER_MINUTE": "2"}
    with _client(environment) as client:
        statuses = [_login(client, "wrong-token-of-enough-length") for _ in range(2)]
        statuses.append(_login(client))

    assert statuses == [401, 401, 429]


@pytest.mark.requirement("SEC-06", "SEC-12")
def test_the_session_and_the_key_share_one_quota(valid_environment: dict[str, str]) -> None:
    """One principal behind both credentials: a browser and a script count together."""
    environment = {**valid_environment, "SEXTANTE_RATE_LIMIT_GENERAL_PER_MINUTE": "2"}
    with _client(environment) as client:
        _login(client)
        by_session = client.get("/api/jobs/unknown").status_code
        client.cookies.clear()
        by_key = [
            client.get("/api/jobs/unknown", headers={"X-API-Key": SYNTHETIC_API_KEY}).status_code
            for _ in range(2)
        ]

    assert (by_session, by_key) == (404, [404, 429])


@pytest.mark.requirement("SEC-15", "SEC-06")
def test_a_refused_token_never_reaches_the_log(
    valid_environment: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    """The refusal is logged by its event only, never with the token that was sent."""
    with _client(valid_environment) as client:
        capsys.readouterr()
        _login(client, "leaked-token-value-1234")
        _login(client)

    output = capsys.readouterr().out
    assert "access_token_rejected" in output
    assert "session_opened" in output
    assert "leaked-token-value-1234" not in output
    assert SYNTHETIC_ACCESS_TOKEN not in output


@pytest.mark.requirement("REQ-PLT-007", "SEC-02")
@pytest.mark.parametrize("token", [None, "short"])
def test_a_missing_or_short_access_token_refuses_startup(
    valid_environment: dict[str, str], token: str | None
) -> None:
    """Without a token of enough length the server never starts, naming the variable."""
    environment = {k: v for k, v in valid_environment.items() if k != "SEXTANTE_ACCESS_TOKEN"}
    if token is not None:
        environment["SEXTANTE_ACCESS_TOKEN"] = token

    with pytest.raises(StartupConfigurationError, match="SEXTANTE_ACCESS_TOKEN"):
        create_app(environment)

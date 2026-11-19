"""Decision 3.27: deploy.sh against a local stand-in of the ShardCloud API.

The stand-in answers like the endpoints of ShardCloud's OpenAPI document (backup, image
rebuild and status, app status) and serves a health check, so the script's order, its
stops and its handling of the token are tested without the real service.
"""

import json
import os
import subprocess
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Final

import pytest

DEPLOY: Final = Path(__file__).resolve().parents[3] / "deploy" / "shardcloud" / "deploy.sh"
TOKEN: Final = "synthetic-shardcloud-token-for-tests"  # noqa: S105 - not a real secret
APP: Final = "11111111-1111-1111-1111-111111111111"
IMAGE: Final = "22222222-2222-2222-2222-222222222222"


@dataclass
class StandIn:
    """What the stand-in answers, and every call it received."""

    backup_status: int = 200
    build_statuses: list[str] = field(default_factory=lambda: ["building", "success"])
    served_version: str = "1.2.0"
    calls: list[tuple[str, str, str]] = field(default_factory=list)


def _answer_for(state: StandIn, method: str, path: str) -> tuple[int, object]:
    # The stand-in's routes: health of the site, backup, image status; the rest is accepted.
    if path == "/health-site/api/health":
        return 200, {"status": "ok", "version": state.served_version}
    if path == f"/api/project/{APP}/backups":
        return state.backup_status, {"backup": {}}
    if path == f"/api/custom-images/{IMAGE}" and method == "GET":
        statuses = state.build_statuses
        return 200, {"id": IMAGE, "status": statuses.pop(0) if len(statuses) > 1 else statuses[0]}
    return 200, {}


class _StandInServer(ThreadingHTTPServer):
    state: StandIn


class _Handler(BaseHTTPRequestHandler):
    server: _StandInServer

    def log_message(self, *_: object) -> None:
        return

    def _route(self, method: str) -> None:
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        state = self.server.state
        state.calls.append((method, self.path, self.headers.get("Authorization", "")))
        status, body = _answer_for(state, method, self.path)
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:
        self._route("GET")

    def do_POST(self) -> None:
        self._route("POST")

    def do_PUT(self) -> None:
        self._route("PUT")


@contextmanager
def _stand_in(state: StandIn) -> Iterator[str]:
    server = _StandInServer(("127.0.0.1", 0), _Handler)
    server.state = state
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def _deploy(base: str, tmp_path: Path, version: str = "1.2.0") -> subprocess.CompletedProcess[str]:
    context = tmp_path / "context.zip"
    context.write_bytes(b"PK synthetic context")
    environment = os.environ | {
        "SHARD_CLOUD_API_KEY": TOKEN,
        "SHARDCLOUD_APP_ID": APP,
        "SHARDCLOUD_IMAGE_ID": IMAGE,
        "SHARDCLOUD_URL": f"{base}/health-site",
        "SHARDCLOUD_API_URL": f"{base}/api",
        "SHARDCLOUD_POLL_SECONDS": "0",
    }
    return subprocess.run(  # noqa: S603 - fixed script, synthetic arguments
        ["bash", str(DEPLOY), str(context), version],  # noqa: S607
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


@pytest.mark.requirement("D-3.27")
def test_a_release_is_backed_up_rebuilt_restarted_and_checked_in_that_order(
    tmp_path: Path,
) -> None:
    """Backup first; the restart waits for a successful build; the version must answer."""
    state = StandIn()
    with _stand_in(state) as base:
        result = _deploy(base, tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    shard_calls = [(m, p) for m, p, _ in state.calls if p.startswith("/api/")]
    assert shard_calls == [
        ("POST", f"/api/project/{APP}/backups"),
        ("PUT", f"/api/custom-images/{IMAGE}"),
        ("GET", f"/api/custom-images/{IMAGE}"),
        ("GET", f"/api/custom-images/{IMAGE}"),
        ("POST", f"/api/apps/{APP}/status"),
    ]
    assert all(auth == f"Bearer {TOKEN}" for _, p, auth in state.calls if p.startswith("/api/"))


@pytest.mark.requirement("D-3.27")
def test_a_failed_backup_stops_the_deploy_before_anything_changes(tmp_path: Path) -> None:
    """No rebuild, no restart."""
    state = StandIn(backup_status=500)
    with _stand_in(state) as base:
        result = _deploy(base, tmp_path)

    assert result.returncode != 0
    assert [p for _, p, _ in state.calls] == [f"/api/project/{APP}/backups"]


@pytest.mark.requirement("D-3.27")
def test_a_failed_build_stops_before_the_restart(tmp_path: Path) -> None:
    """The running release keeps running."""
    state = StandIn(build_statuses=["failed"])
    with _stand_in(state) as base:
        result = _deploy(base, tmp_path)

    assert result.returncode != 0
    assert not any(p.endswith("/status") for _, p, _ in state.calls)


@pytest.mark.requirement("D-3.27", "SEC-15")
def test_the_token_never_reaches_the_output(tmp_path: Path) -> None:
    """It goes to curl on standard input, and the script prints no request."""
    state = StandIn()
    with _stand_in(state) as base:
        result = _deploy(base, tmp_path)

    assert TOKEN not in result.stdout + result.stderr

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
    # Backups the app already holds, as (id, created); each is done.
    existing_backups: list[tuple[str, str]] = field(default_factory=list)
    delete_status: int = 200
    build_statuses: list[str] = field(default_factory=lambda: ["building", "success"])
    served_version: str = "1.2.0"
    calls: list[tuple[str, str, str]] = field(default_factory=list)
    rebuilt: bool = False
    new_backup_polls: int = 0


NEW_BACKUP: Final = "33333333-3333-3333-3333-333333333333"
BACKUPS: Final = f"/api/project/{APP}/backups"
IMAGE_PATH: Final = f"/api/custom-images/{IMAGE}"


def _backups(state: StandIn) -> list[dict[str, object]]:
    held: list[dict[str, object]] = [
        {"id": backup_id, "created": created, "done": True}
        for backup_id, created in state.existing_backups
    ]
    if any(method == "POST" and path == BACKUPS for method, path, _ in state.calls):
        # The new backup is reported running once, then done.
        state.new_backup_polls += 1
        held.append(
            {
                "id": NEW_BACKUP,
                "created": "2026-11-19T10:00:00Z",
                "done": state.new_backup_polls > 1,
            }
        )
    return held


def _image(state: StandIn) -> dict[str, object]:
    if not state.rebuilt:
        return {"id": IMAGE, "status": "success", "updated_at": "2026-11-01T00:00:00Z"}
    statuses = state.build_statuses
    status = statuses.pop(0) if len(statuses) > 1 else statuses[0]
    return {"id": IMAGE, "status": status, "updated_at": "2026-11-19T10:05:00Z"}


def _answer_for(state: StandIn, method: str, path: str) -> tuple[int, object]:
    # The stand-in's routes, shaped like ShardCloud's OpenAPI document.
    if path == "/health-site/api/health":
        return 200, {"status": "ok", "version": state.served_version}
    if path == BACKUPS and method == "GET":
        return 200, {"backups": _backups(state)}
    if path == BACKUPS and method == "POST":
        return state.backup_status, {"backup": {"id": NEW_BACKUP, "done": False}}
    if path.startswith(f"{BACKUPS}/") and method == "DELETE":
        if state.delete_status == 200:
            state.existing_backups = [b for b in state.existing_backups if not path.endswith(b[0])]
        return state.delete_status, {}
    if path == IMAGE_PATH and method == "PUT":
        state.rebuilt = True
        return 200, {"id": IMAGE, "status": "building"}
    if path == IMAGE_PATH:
        return 200, _image(state)
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

    def do_DELETE(self) -> None:
        self._route("DELETE")


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


def _shard_calls(state: StandIn) -> list[tuple[str, str]]:
    return [(method, path) for method, path, _ in state.calls if path.startswith("/api/")]


@pytest.mark.requirement("D-3.27")
def test_a_release_is_backed_up_rebuilt_restarted_and_checked_in_that_order(
    tmp_path: Path,
) -> None:
    """A finished backup first; the restart waits for a new build; the version must answer."""
    state = StandIn()
    with _stand_in(state) as base:
        result = _deploy(base, tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    calls = _shard_calls(state)
    order = [
        calls.index(call)
        for call in [
            ("POST", BACKUPS),
            ("PUT", IMAGE_PATH),
            ("POST", f"/api/apps/{APP}/status"),
        ]
    ]
    assert order == sorted(order)
    # The backup was polled until done before the rebuild started.
    assert state.new_backup_polls >= 2
    assert calls.index(("PUT", IMAGE_PATH)) > max(
        i for i, call in enumerate(calls) if call == ("GET", BACKUPS)
    )
    assert all(auth == f"Bearer {TOKEN}" for _, p, auth in state.calls if p.startswith("/api/"))


@pytest.mark.requirement("D-3.27")
def test_a_stale_successful_build_does_not_count(tmp_path: Path) -> None:
    """The build before the deploy said success; only a newer one may lead to the restart."""
    state = StandIn(build_statuses=["building", "building", "success"])
    with _stand_in(state) as base:
        result = _deploy(base, tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    image_reads_after_put = [
        c
        for c in _shard_calls(state)[_shard_calls(state).index(("PUT", IMAGE_PATH)) :]
        if c == ("GET", IMAGE_PATH)
    ]
    assert len(image_reads_after_put) == 3


@pytest.mark.requirement("D-3.27")
def test_at_the_limit_the_oldest_backup_makes_room(tmp_path: Path) -> None:
    """Ten backups held: the oldest is deleted before the new one."""
    held = [(f"b{n:02d}", f"2026-11-{n:02d}T00:00:00Z") for n in range(1, 11)]
    state = StandIn(existing_backups=held)
    with _stand_in(state) as base:
        result = _deploy(base, tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    deletes = [p for m, p in _shard_calls(state) if m == "DELETE"]
    assert deletes == [f"{BACKUPS}/b01"]


@pytest.mark.requirement("D-3.27")
def test_no_room_for_a_backup_stops_the_deploy(tmp_path: Path) -> None:
    """ShardCloud refuses to delete a backup too young: nothing else happens."""
    held = [(f"b{n:02d}", f"2026-11-{n:02d}T00:00:00Z") for n in range(1, 11)]
    state = StandIn(existing_backups=held, delete_status=403)
    with _stand_in(state) as base:
        result = _deploy(base, tmp_path)

    assert result.returncode != 0
    assert ("POST", BACKUPS) not in _shard_calls(state)
    assert ("PUT", IMAGE_PATH) not in _shard_calls(state)


@pytest.mark.requirement("D-3.27")
def test_a_failed_backup_stops_the_deploy_before_anything_changes(tmp_path: Path) -> None:
    """No rebuild, no restart."""
    state = StandIn(backup_status=500)
    with _stand_in(state) as base:
        result = _deploy(base, tmp_path)

    assert result.returncode != 0
    assert all(
        method in {"GET", "POST"} and path == BACKUPS for method, path in _shard_calls(state)
    )


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

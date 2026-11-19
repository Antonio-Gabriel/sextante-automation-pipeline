"""Decision 3.28: the release reaches ShardCloud through the deploy repository.

push_context.sh is run against a local bare git repository, and wait_for_release.sh
against a local server standing in for the app's public address. Nothing here calls
ShardCloud or GitHub.
"""

import json
import os
import subprocess
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import ClassVar, Final

import pytest

SHARDCLOUD: Final = Path(__file__).resolve().parents[3] / "deploy" / "shardcloud"
# GitHub's published ed25519 host key (api.github.com/meta, "ssh_keys").
GITHUB_ED25519: Final = "AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl"


def _run(*command: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603 - fixed scripts and synthetic arguments
        list(command), env=env, capture_output=True, text=True, timeout=60, check=False
    )


def _context(path: Path, files: dict[str, str]) -> Path:
    for name, content in files.items():
        (path / name).parent.mkdir(parents=True, exist_ok=True)
        (path / name).write_text(content)
    return path


def _push(remote: Path, context: Path, version: str) -> subprocess.CompletedProcess[str]:
    env = os.environ | {"SHARDCLOUD_DEPLOY_REMOTE": str(remote)}
    env.pop("SHARDCLOUD_DEPLOY_KEY", None)
    return _run("bash", str(SHARDCLOUD / "push_context.sh"), str(context), version, env=env)


def _main_of(remote: Path, tmp_path: Path) -> tuple[set[str], str]:
    clone = tmp_path / "check"
    _run("git", "clone", "--quiet", str(remote), str(clone))
    files = {
        str(p.relative_to(clone)) for p in clone.rglob("*") if ".git" not in p.parts and p.is_file()
    }
    log = _run("git", "-C", str(clone), "log", "--format=%s").stdout
    return files, log


@pytest.mark.requirement("D-3.28")
def test_each_release_replaces_the_deploy_repository_whole(tmp_path: Path) -> None:
    """Dockerfile at the root, files of the previous release gone, one commit per version."""
    remote = tmp_path / "deploy.git"
    _run("git", "init", "--quiet", "--bare", "--initial-branch", "main", str(remote))
    first = _context(tmp_path / "c1", {"Dockerfile": "FROM a", "old.txt": "x", "src/app.py": "1"})
    second = _context(tmp_path / "c2", {"Dockerfile": "FROM b", "src/app.py": "2"})

    pushed = [_push(remote, first, "1.0.0"), _push(remote, second, "1.1.0")]
    files, log = _main_of(remote, tmp_path)

    assert [r.returncode for r in pushed] == [0, 0], [r.stderr for r in pushed]
    assert files == {"Dockerfile", "src/app.py"}
    assert log.splitlines() == ["Release 1.1.0", "Release 1.0.0"]


@pytest.mark.requirement("D-3.28")
def test_a_context_without_a_dockerfile_at_its_root_is_never_pushed(tmp_path: Path) -> None:
    """ShardCloud builds the root; anything else would fail there, after the push."""
    remote = tmp_path / "deploy.git"
    _run("git", "init", "--quiet", "--bare", "--initial-branch", "main", str(remote))
    context = _context(tmp_path / "c", {"deploy/Dockerfile": "FROM a"})

    result = _push(remote, context, "1.0.0")

    assert result.returncode != 0
    assert _run("git", "-C", str(remote), "rev-parse", "main").returncode != 0


@pytest.mark.requirement("D-3.28", "SEC-06")
def test_github_is_reached_only_with_its_pinned_host_key() -> None:
    """The deploy key is never offered to a host that is not github.com's own."""
    script = (SHARDCLOUD / "push_context.sh").read_text()

    assert "StrictHostKeyChecking=yes" in script
    assert f"github.com ssh-ed25519 {GITHUB_ED25519}" in script


class _Health(BaseHTTPRequestHandler):
    versions: ClassVar[list[str]] = []

    def log_message(self, *_: object) -> None:
        return

    def do_GET(self) -> None:
        version = self.versions.pop(0) if len(self.versions) > 1 else self.versions[0]
        payload = json.dumps({"status": "ok", "version": version}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


@contextmanager
def _site(versions: list[str]) -> Iterator[str]:
    handler = type("Health", (_Health,), {"versions": list(versions)})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def _wait(url: str, version: str, minutes: str) -> subprocess.CompletedProcess[str]:
    env = os.environ | {"SHARDCLOUD_POLL_SECONDS": "0"}
    return _run("bash", str(SHARDCLOUD / "wait_for_release.sh"), url, version, minutes, env=env)


@pytest.mark.requirement("D-3.28")
def test_the_deploy_ends_when_the_public_address_answers_the_new_version() -> None:
    """The old version answers until a person restarts the app; then the new one."""
    with _site(["1.0.0", "1.0.0", "1.1.0"]) as url:
        result = _wait(url, "1.1.0", "1")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Release 1.1.0 is live" in result.stdout


@pytest.mark.requirement("D-3.28")
def test_the_deploy_fails_when_the_new_version_never_answers() -> None:
    """After the wait, the job says what to check."""
    with _site(["1.0.0"]) as url:
        result = _wait(url, "1.1.0", "0")

    assert result.returncode != 0
    assert "restarted" in result.stderr

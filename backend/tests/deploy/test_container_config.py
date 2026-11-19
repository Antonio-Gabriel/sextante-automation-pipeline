"""Deploy tickets 01 and 02: the container rules, read from the files that build them.

These tests read compose.yaml, the Dockerfiles and the nginx configuration; they start no
container. The running checks (health, a job that survives a restart, the headers
served, signing in through the frontend) are recorded in the CHG entries.
"""

import re
import subprocess
from pathlib import Path
from typing import Any, Final

import pytest
import yaml

REPOSITORY: Final = Path(__file__).resolve().parents[3]
COMPOSE: Final = REPOSITORY / "compose.yaml"
DOCKERFILES: Final = sorted(REPOSITORY.glob("*/Dockerfile"))
SERVICES: Final = ("api", "web")
# Addresses that listen on every interface, IPv4 and IPv6.
EVERY_INTERFACE: Final = re.compile(r"0\.0\.0\.0|\[::\]|--host[ =]::")
# The one file allowed to name one, under decision 3.26 (docs/00).
EVERY_INTERFACE_ALLOWED_IN: Final = "backend/Dockerfile"
# Text that explains the rule, rather than configures a listener.
EXPLAINING: Final = (".md",)
THIS_FILE: Final = str(Path(__file__).resolve().relative_to(REPOSITORY))
# SEC-11 §11.2: every header the served frontend must carry.
SECURITY_HEADERS: Final = (
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
    "Cross-Origin-Opener-Policy",
    "Cross-Origin-Resource-Policy",
)
NGINX: Final = REPOSITORY / "frontend" / "nginx"


def _services() -> dict[str, Any]:
    services: dict[str, Any] = yaml.safe_load(COMPOSE.read_text())["services"]
    return services


def _tracked_files() -> list[str]:
    listing = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        check=True,
    )
    return listing.stdout.splitlines()


def _base_images(dockerfile: Path) -> list[str]:
    text = dockerfile.read_text()
    arguments = dict(re.findall(r"^ARG\s+(\w+)=(\S+)", text, flags=re.MULTILINE))
    bases = re.findall(r"^FROM\s+(\S+)", text, flags=re.MULTILINE)
    return [re.sub(r"\$\{(\w+)\}", lambda m: arguments.get(m[1], m[0]), base) for base in bases]


@pytest.mark.requirement("SEC-06", "D-3.26")
def test_every_published_port_is_on_127_0_0_1_only() -> None:
    """Nothing is reachable from another machine."""
    ports = [port for service in _services().values() for port in service.get("ports", [])]

    assert ports
    assert all(str(port).startswith("127.0.0.1:") for port in ports), ports


@pytest.mark.requirement("SEC-06", "D-3.26")
def test_only_the_api_image_listens_on_every_interface() -> None:
    """The container needs it; the exception lives in one file of the repository."""
    found = sorted(
        name
        for name in _tracked_files()
        if not name.endswith(EXPLAINING)
        and name != THIS_FILE
        and (REPOSITORY / name).is_file()
        and EVERY_INTERFACE.search((REPOSITORY / name).read_text(errors="ignore"))
    )

    assert found == [EVERY_INTERFACE_ALLOWED_IN]
    # Without Docker, the server keeps to 127.0.0.1.
    assert "--host 127.0.0.1" in (REPOSITORY / "backend" / "Makefile").read_text()


@pytest.mark.requirement("SEC-04", "D-3.26")
@pytest.mark.parametrize("name", SERVICES)
def test_each_container_is_locked_down(name: str) -> None:
    """Read-only root, no capabilities, no privilege gain, bounded, a private /tmp."""
    service = _services()[name]

    assert service["read_only"] is True
    assert service["cap_drop"] == ["ALL"]
    assert "no-new-privileges:true" in service["security_opt"]
    [tmp] = service["tmpfs"]
    assert tmp.startswith("/tmp:") and {"noexec", "nosuid", "nodev"} <= set(tmp.split(","))  # noqa: S108
    assert service["pids_limit"] and service["mem_limit"]


@pytest.mark.requirement("SEC-02", "SEC-03")
@pytest.mark.parametrize("context", ["backend", "frontend"])
def test_no_secret_or_local_data_enters_an_image(context: str) -> None:
    """Secrets come from config/.env when the API starts; build contexts never take it."""
    ignore = (REPOSITORY / context / ".dockerignore").read_text().splitlines()

    assert "*" in ignore or ".env*" in ignore
    assert not any(line.startswith("!") and ".env" in line for line in ignore)
    assert _services()["api"]["env_file"] == "config/.env"
    assert "env_file" not in _services()["web"]


@pytest.mark.requirement("SEC-20", "D-3.26")
@pytest.mark.parametrize("dockerfile", DOCKERFILES, ids=lambda path: path.parent.name)
def test_base_images_are_pinned_by_digest_and_run_without_root(dockerfile: Path) -> None:
    """A moved tag never changes the build; the last stage never runs as root."""
    bases = _base_images(dockerfile)
    users = re.findall(r"^USER\s+(\S+)", dockerfile.read_text(), flags=re.MULTILINE)

    assert bases and all(re.search(r"@sha256:[0-9a-f]{64}$", base) for base in bases), bases
    assert users and users[-1].split(":")[0] not in {"root", "0"}


@pytest.mark.requirement("SEC-20")
def test_the_api_dependencies_install_from_the_hashed_lock() -> None:
    """Every runtime dependency of pyproject.toml is pinned there, by version and hash."""
    backend = REPOSITORY / "backend"
    lock = (backend / "requirements.lock").read_text()
    declared = re.findall(r'^\s+"([A-Za-z0-9_.-]+)', _dependencies_block(backend), re.MULTILINE)
    pinned = {m.lower() for m in re.findall(r"^([A-Za-z0-9_.-]+)==", lock, flags=re.MULTILINE)}

    assert "--require-hashes" in (backend / "Dockerfile").read_text()
    assert {name.lower() for name in declared} <= pinned
    assert all("--hash=sha256:" in entry for entry in lock.split("==")[1:])


def _dependencies_block(backend: Path) -> str:
    text = (backend / "pyproject.toml").read_text()
    return text.split("dependencies = [", 1)[1].split("]", 1)[0]


@pytest.mark.requirement("REQ-PLT-008", "D-3.26")
def test_the_data_survive_in_a_volume_and_the_reference_files_are_read_only() -> None:
    """Database and uploads in the named volume; catalog and denylist mounted read-only."""
    service = _services()["api"]
    environment = service["environment"]

    assert "sextante-data:/data" in service["volumes"]
    assert environment["SEXTANTE_DATABASE_URL"].endswith("////data/sextante.db")
    assert environment["SEXTANTE_UPLOAD_DIR"] == "/data/uploads"
    reference = [v for v in service["volumes"] if v.startswith("./")]
    assert reference and all(v.endswith(":ro") for v in reference)


@pytest.mark.requirement("SEC-11")
def test_the_served_frontend_carries_every_security_header_in_every_location() -> None:
    """The headers of §11.2, and no location that drops them."""
    headers = (NGINX / "security-headers.conf").read_text()
    server = (NGINX / "default.conf").read_text()
    locations = re.findall(r"location\s+\S+\s*\{(.*?)\n    \}", server, flags=re.DOTALL)

    assert all(f'add_header {name} "' in headers for name in SECURITY_HEADERS)
    assert "Content-Security-Policy-Report-Only" not in headers
    assert locations and all("security-headers.conf" in body for body in locations)
    assert "server_tokens off;" in server


@pytest.mark.requirement("SEC-11", "SEC-06")
def test_the_frontend_forwards_the_api_on_the_same_origin() -> None:
    """/api goes to the API container, so the session cookie works and there is no CORS."""
    server = (NGINX / "default.conf").read_text()

    assert "location /api/ {" in server
    assert "set $api_upstream http://api:8000;" in server
    assert "Access-Control-Allow-Origin" not in server

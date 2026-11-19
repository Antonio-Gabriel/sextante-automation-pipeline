"""Deploy tickets 01 and 02: the container rules, read from the files that build them.

These tests read compose.yaml and the Dockerfiles; they start no container. The running
check (health, a job that survives a restart) is in the README and in CHG entries.
"""

import re
from pathlib import Path
from typing import Any, Final

import pytest
import yaml

REPOSITORY: Final = Path(__file__).resolve().parents[3]
COMPOSE: Final = REPOSITORY / "compose.yaml"
DOCKERFILES: Final = sorted(REPOSITORY.glob("*/Dockerfile"))
LISTEN_EVERYWHERE: Final = "0.0.0.0"  # noqa: S104 - the address this test hunts for
# The one file allowed to name it, under decision 3.26 (docs/00).
ALLOWED_LISTEN_EVERYWHERE: Final = REPOSITORY / "backend" / "Dockerfile"
# What runs or configures a listener; the docs that explain the rule are not among them.
LISTENER_FILES: Final = (
    "compose.yaml",
    "backend/Makefile",
    "backend/Dockerfile",
    "frontend/Dockerfile",
    "frontend/vite.config.ts",
    "frontend/nginx/*.conf",
    "backend/src/**/*.py",
)


def _services() -> dict[str, Any]:
    services: dict[str, Any] = yaml.safe_load(COMPOSE.read_text())["services"]
    return services


@pytest.mark.requirement("SEC-06", "D-3.26")
def test_every_published_port_is_on_127_0_0_1_only() -> None:
    """Nothing is reachable from another machine."""
    ports = [port for service in _services().values() for port in service.get("ports", [])]

    assert ports
    assert all(str(port).startswith("127.0.0.1:") for port in ports), ports


@pytest.mark.requirement("SEC-06", "D-3.26")
def test_only_the_api_image_listens_on_every_interface() -> None:
    """The container needs it; the exception lives in one file, nowhere else."""
    found = sorted(
        str(path.relative_to(REPOSITORY))
        for pattern in LISTENER_FILES
        for path in REPOSITORY.glob(pattern)
        if LISTEN_EVERYWHERE in path.read_text()
    )

    assert found == [str(ALLOWED_LISTEN_EVERYWHERE.relative_to(REPOSITORY))]
    # Without Docker, the server keeps to 127.0.0.1.
    assert "--host 127.0.0.1" in (REPOSITORY / "backend" / "Makefile").read_text()


@pytest.mark.requirement("SEC-04", "D-3.26")
@pytest.mark.parametrize("name", ["api"])
def test_each_container_is_locked_down(name: str) -> None:
    """Read-only root, no capabilities, no privilege gain, a writable /tmp only."""
    service = _services()[name]

    assert service["read_only"] is True
    assert service["cap_drop"] == ["ALL"]
    assert "no-new-privileges:true" in service["security_opt"]
    assert service["tmpfs"] == ["/tmp"]  # noqa: S108 - a private tmpfs, not a shared /tmp


@pytest.mark.requirement("SEC-02", "SEC-03")
def test_secrets_come_from_config_env_at_start_never_from_the_image() -> None:
    """The env file is read by compose; the build context lets in code only."""
    assert _services()["api"]["env_file"] == "config/.env"
    ignore = (REPOSITORY / "backend" / ".dockerignore").read_text().splitlines()
    assert "*" in ignore
    assert not any(".env" in line and line.startswith("!") for line in ignore)


@pytest.mark.requirement("SEC-20", "D-3.26")
@pytest.mark.parametrize("dockerfile", DOCKERFILES, ids=lambda path: path.parent.name)
def test_base_images_are_pinned_by_digest_and_run_without_root(dockerfile: Path) -> None:
    """A moved tag never changes the build; the last stage never runs as root."""
    text = dockerfile.read_text()
    bases = re.findall(r"^FROM\s+(\S+)", text, flags=re.MULTILINE)
    users = re.findall(r"^USER\s+(\S+)", text, flags=re.MULTILINE)

    assert bases and all(re.search(r"@sha256:[0-9a-f]{64}$", base) for base in bases), bases
    assert users and users[-1].split(":")[0] not in {"root", "0"}


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

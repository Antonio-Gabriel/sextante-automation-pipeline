"""Deploy tickets 01 and 02: the container rules, read from the files that build them.

These tests read compose.yaml, the Dockerfiles and the nginx configuration; they start no
container. The running checks (health, a job that survives a restart, the headers
served, signing in through the frontend) are recorded in the CHG entries.
"""

import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any, Final

import pytest
import yaml

REPOSITORY: Final = Path(__file__).resolve().parents[3]
COMPOSE: Final = REPOSITORY / "compose.yaml"
DOCKERFILES: Final = sorted(
    path for path in REPOSITORY.glob("**/Dockerfile") if "node_modules" not in path.parts
)
SHARDCLOUD: Final = REPOSITORY / "deploy" / "shardcloud"
SERVICES: Final = ("api", "web")
# Addresses that listen on every interface, IPv4 and IPv6.
EVERY_INTERFACE: Final = re.compile(r"0\.0\.0\.0|\[::\]|--host[ =]::")
# The two listeners inside a container, under decision 3.26 (docs/00): there a process on
# 127.0.0.1 receives nothing from a published port.
EVERY_INTERFACE_ALLOWED_IN: Final = [
    "backend/Dockerfile",
    "deploy/shardcloud/nginx.conf",
    "frontend/nginx/default.conf",
]
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
# The servers that answer browsers: compose's web container and the ShardCloud image.
SERVED_CONFIGS: Final = (NGINX / "default.conf", SHARDCLOUD / "nginx.conf")


@pytest.mark.requirement("SEC-06", "D-3.26")
def test_every_nginx_listener_names_its_address() -> None:
    """A bare `listen 8080;` means every interface without saying so; the guard needs it said."""
    listens = [
        line.strip()
        for conf in SERVED_CONFIGS
        for line in conf.read_text().splitlines()
        if line.strip().startswith("listen ")
    ]

    assert listens
    assert all(re.match(r"listen\s+[\d.]+:\d+;", line) for line in listens), listens


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
def test_only_the_container_listeners_listen_on_every_interface() -> None:
    """The containers need it; the exception lives in their two files only."""
    found = sorted(
        name
        for name in _tracked_files()
        if not name.endswith(EXPLAINING)
        and name != THIS_FILE
        and (REPOSITORY / name).is_file()
        and EVERY_INTERFACE.search((REPOSITORY / name).read_text(errors="ignore"))
    )

    assert found == EVERY_INTERFACE_ALLOWED_IN
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
def test_base_images_are_pinned_by_digest(dockerfile: Path) -> None:
    """A moved tag never changes the build."""
    bases = _base_images(dockerfile)

    assert bases and all(re.search(r"@sha256:[0-9a-f]{64}$", base) for base in bases), bases


@pytest.mark.requirement("SEC-04", "D-3.26")
@pytest.mark.parametrize("context", ["backend", "frontend"])
def test_the_compose_images_run_without_root(context: str) -> None:
    """The last stage of each compose image switches to an unprivileged user."""
    text = (REPOSITORY / context / "Dockerfile").read_text()
    users = re.findall(r"^USER\s+(\S+)", text, flags=re.MULTILINE)

    assert users and users[-1].split(":")[0] not in {"root", "0"}


@pytest.mark.requirement("SEC-04", "D-3.27")
def test_the_shardcloud_image_drops_root_where_the_platform_allows_it() -> None:
    """Where it can, the API runs as uid 10001 without capabilities and nginx workers as
    www-data; always on 127.0.0.1, and never failing where users cannot be changed."""
    entrypoint = (SHARDCLOUD / "entrypoint.sh").read_text()
    nginx = (SHARDCLOUD / "nginx.conf").read_text()

    assert "setpriv --reuid=sextante --regid=sextante --init-groups --inh-caps=-all" in entrypoint
    assert "--host 127.0.0.1 --port 8000" in entrypoint
    assert "umask 077" in entrypoint
    # The workers switch to www-data only where changing user works; never set in the file.
    assert 'nginx_globals="daemon off; user www-data;"' in entrypoint
    assert not re.search(r"^user ", nginx, flags=re.MULTILINE)
    assert "proxy_pass http://127.0.0.1:8000;" in nginx


@pytest.mark.requirement("SEC-15", "D-3.27")
def test_the_shardcloud_image_hides_the_api_description() -> None:
    """The public server does not describe its API to everyone."""
    assert "SEXTANTE_API_DOCS_ENABLED=false" in (SHARDCLOUD / "Dockerfile").read_text()


@pytest.mark.requirement("SEC-20")
def test_the_api_dependencies_install_from_the_hashed_lock() -> None:
    """Every runtime dependency of pyproject.toml is pinned there, by version and hash."""
    backend = REPOSITORY / "backend"
    lock = (backend / "requirements.lock").read_text()
    project = tomllib.loads((backend / "pyproject.toml").read_text())["project"]
    declared = [re.split(r"[<>=\[;\s]", entry, maxsplit=1)[0] for entry in project["dependencies"]]
    pinned = {m.lower() for m in re.findall(r"^([A-Za-z0-9_.-]+)==", lock, flags=re.MULTILINE)}

    assert "--require-hashes" in (backend / "Dockerfile").read_text()
    assert {name.lower() for name in declared} <= pinned
    assert all("--hash=sha256:" in entry for entry in lock.split("==")[1:])


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
@pytest.mark.parametrize("config", SERVED_CONFIGS, ids=lambda path: path.parent.name)
def test_the_served_frontend_carries_every_security_header_in_every_location(
    config: Path,
) -> None:
    """The headers of §11.2, and no location that drops them."""
    headers = (NGINX / "security-headers.conf").read_text()
    server = config.read_text()
    # Each location block, up to the next one or the end, whatever its indentation.
    locations = re.split(r"^\s*location\s", server, flags=re.MULTILINE)[1:]

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


@pytest.mark.requirement("SEC-20", "D-3.27")
def test_the_shardcloud_context_holds_every_file_its_dockerfile_copies(tmp_path: Path) -> None:
    """The file list of build_context.sh and the COPY lines of the Dockerfile agree."""
    script = SHARDCLOUD / "build_context.sh"
    subprocess.run([str(script), str(tmp_path / "context")], cwd=REPOSITORY, check=True)  # noqa: S603
    dockerfile = (tmp_path / "context" / "Dockerfile").read_text()
    sources = [
        line.split()[1]
        for line in dockerfile.splitlines()
        if line.startswith("COPY ") and "--from=" not in line
    ]

    assert sources
    missing = [source for source in sources if not (tmp_path / "context" / source).exists()]
    assert missing == []


@pytest.mark.requirement("D-3.27")
def test_the_context_carries_its_version_because_shardcloud_passes_no_build_argument(
    tmp_path: Path,
) -> None:
    """ShardCloud builds the zip as it is: the health check must still say X.Y.Z."""
    script = SHARDCLOUD / "build_context.sh"
    subprocess.run([str(script), str(tmp_path / "c"), "HEAD", "1.2.0"], cwd=REPOSITORY, check=True)  # noqa: S603
    refused = subprocess.run(  # noqa: S603
        [str(script), str(tmp_path / "d"), "HEAD", "1.2.0;rm"], cwd=REPOSITORY, check=False
    )

    assert "ARG SEXTANTE_RELEASE_VERSION=1.2.0\n" in (tmp_path / "c" / "Dockerfile").read_text()
    assert refused.returncode != 0


@pytest.mark.requirement("D-3.27", "REQ-PLT-008")
def test_the_shardcloud_image_keeps_nothing_it_needs_in_its_working_directory() -> None:
    """ShardCloud mounts its storage over the working directory: the code lives elsewhere,
    the working directory is the data folder, and the entrypoint sets the paths itself."""
    dockerfile = (SHARDCLOUD / "Dockerfile").read_text()
    entrypoint = (SHARDCLOUD / "entrypoint.sh").read_text()
    workdirs = re.findall(r"^WORKDIR\s+(\S+)", dockerfile, flags=re.MULTILINE)
    runtime = dockerfile.split("FROM ${PYTHON_IMAGE}\n", 1)[1]
    targets = re.findall(r"^COPY\s+(?:--from=\S+\s+)?\S+\s+(\S+)", runtime, flags=re.MULTILINE)

    assert workdirs[-1] == "/data"
    assert targets and not any(target.startswith("/data") for target in targets), targets
    assert 'export PYTHONPATH="/opt/sextante/src"' in entrypoint
    assert "/opt/sextante/VERSION" in entrypoint

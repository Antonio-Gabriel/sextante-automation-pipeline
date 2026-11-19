# Sextante API image (deploy ticket 01). Build from the repository root:
#   docker compose build api
# Base images are pinned by digest: a moved tag never changes what is built (SEC-20).

# --- Build: the dependencies of pyproject.toml in a virtual environment ----------------
FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df AS build

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
WORKDIR /build
COPY pyproject.toml ./
COPY src ./src
# Installs the package to resolve its dependencies, then removes it: the application
# runs from /app/src, next to its migrations (platform/database.py looks for them there).
RUN pip install . && pip uninstall --yes sextante

# --- Runtime: no compiler, no pip cache, no root ---------------------------------------
FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system --gid 10001 sextante \
    && useradd --system --uid 10001 --gid sextante --no-create-home --shell /usr/sbin/nologin sextante \
    && mkdir -p /data /config \
    && chown sextante:sextante /data

COPY --from=build /opt/venv /opt/venv
WORKDIR /app
COPY src ./src
COPY migrations ./migrations

# The database and the uploaded invoices live in this volume, and nowhere else is writable.
VOLUME ["/data"]
USER sextante:sextante
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=20s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"]

# The one place the API listens on every interface: inside its container, where a
# process bound to 127.0.0.1 receives nothing from a published port. The host publishes
# the port on 127.0.0.1 only (compose.yaml). Without Docker, `make run` keeps 127.0.0.1.
# Decision 3.26 of docs/00 (SEC-06).
CMD ["uvicorn", "--factory", "sextante.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]

# Sextante API image (deploy ticket 01). Build from the repository root:
#   docker compose build api
# The base image is pinned by digest, and the dependencies by version and hash
# (requirements.lock): a moved tag or a new release never changes what is built (SEC-20).
ARG PYTHON_IMAGE=python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df

# --- Build: the locked dependencies in a virtual environment ---------------------------
FROM ${PYTHON_IMAGE} AS build

ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
WORKDIR /build
COPY requirements.lock ./
RUN pip install --require-hashes --no-deps -r requirements.lock

# --- Runtime: no build state, no root ----------------------------------------------------
FROM ${PYTHON_IMAGE}

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN groupadd --system --gid 10001 sextante \
    && useradd --system --uid 10001 --gid sextante --no-create-home --shell /usr/sbin/nologin sextante \
    && mkdir -p /data /config \
    && chown sextante:sextante /data \
    && chmod 700 /data

COPY --from=build /opt/venv /opt/venv
WORKDIR /app
# The application runs from /app/src, next to its migrations (platform/database.py).
COPY src ./src
COPY migrations ./migrations

# The database and the uploaded invoices live in this volume, and nowhere else is writable.
VOLUME ["/data"]
USER sextante:sextante
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"]

# umask 077: the database and the invoice files are readable by this user only (SEC-04).
# The one place the API listens on every interface: inside its container, where a
# process bound to 127.0.0.1 receives nothing from a published port. The host publishes
# the port on 127.0.0.1 only (compose.yaml). Without Docker, `make run` keeps 127.0.0.1.
# Decision 3.26 of docs/00 (SEC-06).
CMD ["sh", "-c", "umask 077 && exec uvicorn --factory sextante.main:create_app --host 0.0.0.0 --port 8000 --no-server-header"]

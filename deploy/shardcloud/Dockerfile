# Sextante as one container, for ShardCloud (decision 3.27 of docs/00).
#
# ShardCloud runs one container per app and serves the port 80 over HTTPS. This image
# holds both halves: nginx on port 80 serves the compiled frontend and forwards /api to
# the API, which listens on 127.0.0.1:8000 inside the container only.
#
# Built from the context that build_context.sh assembles from git (repository layout,
# this file at its root). The release pipeline builds the Docker Hub image and zips the
# ShardCloud build from that same context, so both carry the same version.
# Bases pinned by digest and dependencies by hash (SEC-20).
ARG PYTHON_IMAGE=python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df
ARG NODE_IMAGE=node:22-bookworm-slim@sha256:e9f565d32859f0cbfb52125eafe8be39390f24dac302dc3cdf566e8ba3ab21ee

# --- Frontend: type-check and compile -------------------------------------------------
FROM ${NODE_IMAGE} AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund --ignore-scripts
COPY frontend/ ./
RUN npm run build

# --- API: the locked dependencies -------------------------------------------------------
FROM ${PYTHON_IMAGE} AS api
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY backend/requirements.lock /build/requirements.lock
RUN pip install --require-hashes --no-deps -r /build/requirements.lock

# --- Runtime -----------------------------------------------------------------------------
FROM ${PYTHON_IMAGE}

ARG SEXTANTE_RELEASE_VERSION=dev
# nginx pinned to the Debian version tested; when Debian replaces it with a security
# update the build fails, and the pin is raised after testing again (SEC-20).
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        nginx-light=1.22.1-9+deb12u10 nginx=1.22.1-9+deb12u10 \
    && rm -rf /var/lib/apt/lists/* /etc/nginx/sites-enabled /etc/nginx/conf.d \
    && groupadd --system --gid 10001 sextante \
    && useradd --system --uid 10001 --gid sextante --no-create-home --shell /usr/sbin/nologin sextante \
    && mkdir -p /data /config \
    && chown sextante:sextante /data \
    && chmod 700 /data

COPY --from=api /opt/venv /opt/venv
COPY --from=frontend /build/dist /usr/share/sextante/www
WORKDIR /app
COPY backend/src ./src
COPY backend/migrations ./migrations
COPY sources/catalog.xlsx /config/catalog.xlsx
COPY config/entity_denylist.yaml /config/entity_denylist.yaml
COPY deploy/shardcloud/nginx.conf /etc/nginx/nginx.conf
COPY frontend/nginx/security-headers.conf /etc/nginx/snippets/security-headers.conf
COPY deploy/shardcloud/entrypoint.sh /usr/local/bin/sextante-entrypoint

# Settings that are not secrets. The secrets (model key, API key, access token, target
# entity, reviewer) are set as environment variables of the app in ShardCloud.
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TMPDIR=/data/tmp \
    SEXTANTE_DATABASE_URL=sqlite+aiosqlite:////data/sextante.db \
    SEXTANTE_UPLOAD_DIR=/data/uploads \
    SEXTANTE_CATALOG_PATH=/config/catalog.xlsx \
    SEXTANTE_ENTITY_DENYLIST_PATH=/config/entity_denylist.yaml \
    SEXTANTE_API_DOCS_ENABLED=false \
    SEXTANTE_RELEASE_VERSION=${SEXTANTE_RELEASE_VERSION}

LABEL org.opencontainers.image.title="sextante" \
      org.opencontainers.image.version="${SEXTANTE_RELEASE_VERSION}"

EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1/api/health', timeout=2)"]

# Starts as root only to bind port 80 and hand /data to the API's user; the API runs as
# uid 10001 and the nginx workers as www-data (entrypoint.sh).
ENTRYPOINT ["/usr/local/bin/sextante-entrypoint"]

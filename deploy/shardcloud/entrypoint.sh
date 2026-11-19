#!/bin/bash
# Starts the two processes of the ShardCloud container and stops the container when
# either one stops, so the platform restarts it whole (decision 3.27 of docs/00).
#
# It runs as whatever user the platform chooses. ShardCloud runs it as root without
# capabilities: then nothing can change user, and both processes keep the one given. Only
# where changing user works does it hand the data folder to the API's user and drop
# privileges.
set -euo pipefail

# Set here, not only in the image: a platform may start the container without the image's
# environment, and the code is never under the working directory it may mount over.
export PATH="/opt/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export PYTHONPATH="/opt/sextante/src"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export SEXTANTE_CATALOG_PATH="${SEXTANTE_CATALOG_PATH:-/opt/sextante/config/catalog.xlsx}"
export SEXTANTE_ENTITY_DENYLIST_PATH="${SEXTANTE_ENTITY_DENYLIST_PATH:-/opt/sextante/config/entity_denylist.yaml}"
export SEXTANTE_API_DOCS_ENABLED="${SEXTANTE_API_DOCS_ENABLED:-false}"
export SEXTANTE_RELEASE_VERSION="${SEXTANTE_RELEASE_VERSION:-$(cat /opt/sextante/VERSION)}"

# The database and the invoice files are readable by their owner only (SEC-04).
umask 077
data="${SEXTANTE_DATA_DIR:-/data}"
if ! mkdir -p "$data/tmp" "$data/uploads" 2>/dev/null || [[ ! -w "$data" ]]; then
    echo "sextante: the data folder $data is not writable by uid $(id -u)." >&2
    echo "sextante: set SEXTANTE_DATA_DIR to a writable, persistent folder of the platform." >&2
    exit 1
fi
export TMPDIR="$data/tmp"
export SEXTANTE_DATABASE_URL="${SEXTANTE_DATABASE_URL:-sqlite+aiosqlite:///$data/sextante.db}"
export SEXTANTE_UPLOAD_DIR="${SEXTANTE_UPLOAD_DIR:-$data/uploads}"

api_command=(uvicorn --factory sextante.main:create_app --host 127.0.0.1 --port 8000 --no-server-header)
nginx_globals="daemon off; user www-data;"
if setpriv --reuid=sextante --regid=sextante --init-groups true 2>/dev/null; then
    # The data may come back from a backup with other owners: handed back each start.
    chown -R sextante:sextante "$data"
    # The API without root and without capabilities; nginx workers as www-data.
    api_command=(setpriv --reuid=sextante --regid=sextante --init-groups --inh-caps=-all "${api_command[@]}")
else
    # No user can be changed to. A folder left to another owner by an earlier start is
    # taken back if the platform allows it; the start stops above if it stays unwritable.
    if [[ ! -w "$data/tmp" || ! -w "$data/uploads" ]]; then
        # Each folder first, so its content can be read, then everything inside.
        chown "$(id -u):$(id -g)" "$data" "$data"/* 2>/dev/null || true
        chown -R "$(id -u):$(id -g)" "$data" 2>/dev/null || true
    fi
    if [[ ! -w "$data/tmp" || ! -w "$data/uploads" ]]; then
        echo "sextante: $data/tmp or $data/uploads is not writable by uid $(id -u)." >&2
        exit 1
    fi
    # As root, nginx would switch its workers to another user, which needs the
    # capabilities it lacks here: it serves from a single process, as root, instead.
    if [[ "$(id -u)" == "0" ]]; then
        nginx_globals="daemon off; master_process off; user root root;"
    fi
fi

# A stop request before or while both start still stops whatever has started.
api=""
web=""
stop() {
    kill -TERM $api $web 2>/dev/null || true
}
trap stop TERM INT

# The API on this container's 127.0.0.1 only.
"${api_command[@]}" &
api=$!

# nginx on port 80; as root its workers run as www-data (nginx.conf). Its own log goes to
# the standard error from the start, so it never needs a writable /var/log.
nginx -e stderr -g "$nginx_globals" &
web=$!

# The first of the two to stop ends the container, with its status; the other is stopped.
status=0
wait -n "$api" "$web" || status=$?
stop
wait || true
exit "$status"

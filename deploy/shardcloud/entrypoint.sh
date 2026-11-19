#!/bin/bash
# Starts the two processes of the ShardCloud container and stops the container when
# either one stops, so the platform restarts it whole (decision 3.27 of docs/00).
#
# It runs as whatever user the platform chooses: ShardCloud does not run containers as
# root. As root, it hands the data folder to the API's user and drops privileges.
set -euo pipefail

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
if [[ "$(id -u)" == "0" ]]; then
    # The data may come back from a backup with other owners: handed back each start.
    chown -R sextante:sextante "$data"
    # The API without root and without capabilities.
    api_command=(setpriv --reuid=sextante --regid=sextante --init-groups --inh-caps=-all "${api_command[@]}")
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
nginx -e stderr -g "daemon off;" &
web=$!

# The first of the two to stop ends the container, with its status; the other is stopped.
status=0
wait -n "$api" "$web" || status=$?
stop
wait || true
exit "$status"

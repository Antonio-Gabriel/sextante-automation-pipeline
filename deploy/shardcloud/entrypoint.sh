#!/bin/bash
# Starts the two processes of the ShardCloud container and stops the container when
# either one stops, so the platform restarts it whole (decision 3.27 of docs/00).
set -euo pipefail

# The database and the invoice files are readable by the API's user only (SEC-04). The
# data may come back from a backup with other owners: they are handed back each start.
umask 077
mkdir -p /data/tmp /data/uploads
chown -R sextante:sextante /data

# The API, without root and without capabilities, on this container's 127.0.0.1 only.
setpriv --reuid=sextante --regid=sextante --init-groups --inh-caps=-all \
    uvicorn --factory sextante.main:create_app --host 127.0.0.1 --port 8000 \
    --no-server-header &
api=$!

# nginx: its master binds port 80, its workers run as www-data (nginx.conf).
nginx -g "daemon off;" &
web=$!

trap 'kill -TERM "$api" "$web" 2>/dev/null' TERM INT
wait -n "$api" "$web"
status=$?
kill -TERM "$api" "$web" 2>/dev/null || true
exit "$status"

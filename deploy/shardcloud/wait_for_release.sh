#!/bin/bash
# Waits until the public address answers a release's version (decision 3.28 of docs/00).
# ShardCloud rebuilds the image from the deploy repository on its own, but restarting the
# app is done by a person in the dashboard; this waits for that, then confirms it.
#
# Usage: deploy/shardcloud/wait_for_release.sh <https address> <version> [minutes, default 50]
set -euo pipefail

url="$1"
version="$2"
deadline=$((SECONDS + ${3:-50} * 60))
poll_seconds="${SHARDCLOUD_POLL_SECONDS:-20}"

while :; do
    served="$(curl --silent --max-time 10 "$url/api/health" |
        python3 -c 'import json, sys; print(json.load(sys.stdin).get("version", ""))' 2>/dev/null || true)"
    if [[ "$served" == "$version" ]]; then
        echo "Release $version is live at $url."
        exit 0
    fi
    if ((SECONDS >= deadline)); then
        echo "::error::$url still answers version '${served:-none}'. Did the image finish building, and was the app restarted?" >&2
        exit 1
    fi
    echo "Waiting for $version at $url (now: ${served:-no answer})..."
    sleep "$poll_seconds"
done

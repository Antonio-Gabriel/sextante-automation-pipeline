#!/bin/bash
# Waits until the public address answers a release's version (decision 3.28 of docs/00).
# ShardCloud rebuilds the image from the deploy repository on its own, but restarting the
# app is done by a person in the dashboard; this waits for that, then confirms it.
#
# ShardCloud's addresses sit behind Cloudflare, which may answer clients that are not
# browsers with a challenge. That is never worked around (CLAUDE.md): this script then
# stops with code 2 and asks a person to check the version in a browser.
#
# Usage: deploy/shardcloud/wait_for_release.sh <https address> <version> [minutes, default 50]
# Exit: 0 the version answers; 1 it did not in time; 2 a challenge hides the answer.
set -euo pipefail

url="$1"
version="$2"
deadline=$((SECONDS + ${3:-50} * 60))
poll_seconds="${SHARDCLOUD_POLL_SECONDS:-20}"
headers="$(mktemp)"
body="$(mktemp)"
trap 'rm -f "$headers" "$body"' EXIT

while :; do
    curl --silent --max-time 10 --dump-header "$headers" --output "$body" "$url/api/health" || true
    if grep -qi '^cf-mitigated: *challenge' "$headers"; then
        echo "::warning::Cloudflare answers this client with a challenge, so the version cannot be read here." >&2
        echo "Open $url/api/health in a browser: it must show \"version\":\"$version\"." >&2
        exit 2
    fi
    served="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1])).get("version", ""))' "$body" 2>/dev/null || true)"
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

#!/bin/bash
# Publishes one release on ShardCloud (decision 3.27 of docs/00), through its REST API:
#   1. a backup of the app, before anything changes; a failed backup stops the deploy;
#   2. the app's Custom Docker Image rebuilt from the release's build context;
#   3. the app restarted on the new image;
#   4. the public health check answering the release's version.
#
# Usage: deploy/shardcloud/deploy.sh <context.zip> <version>
# Environment: SHARD_CLOUD_API_KEY (secret), SHARDCLOUD_APP_ID, SHARDCLOUD_IMAGE_ID,
#              SHARDCLOUD_URL (the app's public https address).
# The token goes to curl on its standard input, never on a command line or in a log.
set -euo pipefail

context_zip="$1"
version="$2"
# SHARDCLOUD_API_URL only for tests against a local stand-in (tests/deploy).
api="${SHARDCLOUD_API_URL:-https://shardcloud.app/api}"
: "${SHARD_CLOUD_API_KEY:?}" "${SHARDCLOUD_APP_ID:?}" "${SHARDCLOUD_IMAGE_ID:?}" "${SHARDCLOUD_URL:?}"

shard() {
    # shard <method> <path> [curl arguments...]: one authenticated call, failing on 4xx/5xx.
    local method="$1" path="$2"
    shift 2
    printf 'header = "Authorization: Bearer %s"\n' "$SHARD_CLOUD_API_KEY" |
        curl --config - --silent --show-error --fail-with-body --max-time 600 \
            --request "$method" "$api$path" "$@"
}

field() {
    # field <name>: one top-level field of the JSON on standard input.
    python3 -c 'import json, sys; print(json.load(sys.stdin).get(sys.argv[1], ""))' "$1"
}

wait_for() {
    # wait_for <seconds> <description> <command...>: retries every 10 s until it succeeds.
    # SHARDCLOUD_POLL_SECONDS shortens the wait only for tests.
    local deadline=$((SECONDS + $1)) description="$2"
    shift 2
    until "$@"; do
        if ((SECONDS >= deadline)); then
            echo "::error::Timed out waiting for $description." >&2
            return 1
        fi
        sleep "${SHARDCLOUD_POLL_SECONDS:-10}"
    done
}

image_built() {
    local status
    status="$(shard GET "/custom-images/$SHARDCLOUD_IMAGE_ID" | field status)"
    echo "Image build: $status"
    if [[ "$status" == "failed" ]]; then
        echo "::error::ShardCloud could not build the image; see its build logs." >&2
        exit 1
    fi
    [[ "$status" == "success" ]]
}

serving_release() {
    local served
    served="$(curl --silent --max-time 10 "$SHARDCLOUD_URL/api/health" | field version || true)"
    echo "Public health check reports version: ${served:-none}"
    [[ "$served" == "$version" ]]
}

echo "::group::Backup of the app before release $version"
shard POST "/project/$SHARDCLOUD_APP_ID/backups" >/dev/null
echo "Backup created."
echo "::endgroup::"

echo "::group::Rebuild of the image from the release's build context"
shard PUT "/custom-images/$SHARDCLOUD_IMAGE_ID" --form "context=@$context_zip" >/dev/null
wait_for 1800 "the image build" image_built
echo "::endgroup::"

echo "::group::Restart of the app on the new image"
shard POST "/apps/$SHARDCLOUD_APP_ID/status" \
    --header "Content-Type: application/json" --data '{"status":"restart"}' >/dev/null
wait_for 600 "release $version to answer" serving_release
echo "::endgroup::"

echo "Release $version is live at $SHARDCLOUD_URL."

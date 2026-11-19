#!/bin/bash
# Publishes one release on ShardCloud (decision 3.27 of docs/00), through its REST API:
#   1. a finished backup of the app, before anything changes; making room first when the
#      app already holds the most backups ShardCloud keeps. Any failure stops the deploy;
#   2. the app's Custom Docker Image rebuilt from the release's build context, accepted
#      only once ShardCloud reports a build newer than the one before;
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
# SHARDCLOUD_API_URL and SHARDCLOUD_POLL_SECONDS only for tests against a local stand-in.
api="${SHARDCLOUD_API_URL:-https://shardcloud.app/api}"
poll_seconds="${SHARDCLOUD_POLL_SECONDS:-10}"
# ShardCloud keeps up to 10 backups per app (docs.shardcloud.app/apps.md).
max_backups=10
: "${SHARD_CLOUD_API_KEY:?}" "${SHARDCLOUD_APP_ID:?}" "${SHARDCLOUD_IMAGE_ID:?}" "${SHARDCLOUD_URL:?}"

shard() {
    # shard <method> <path> [curl arguments...]: one authenticated call, failing on 4xx/5xx.
    local method="$1" path="$2"
    shift 2
    printf 'header = "Authorization: Bearer %s"\n' "$SHARD_CLOUD_API_KEY" |
        curl --config - --silent --show-error --fail-with-body --max-time 600 \
            --request "$method" "$api$path" "$@"
}

json() {
    # json <python expression over `d` and `a`> [values...]: evaluates a fixed expression of
    # this script on the JSON of standard input; values from outside come in `a`, never
    # inside the expression.
    python3 -c 'import json, sys; d = json.load(sys.stdin); a = sys.argv[2:]; print(eval(sys.argv[1]))' "$@"
}

wait_for() {
    # wait_for <seconds> <description> <command...>: retries until the command succeeds.
    local deadline=$((SECONDS + $1)) description="$2"
    shift 2
    until "$@"; do
        if ((SECONDS >= deadline)); then
            echo "::error::Timed out waiting for $description." >&2
            return 1
        fi
        sleep "$poll_seconds"
    done
}

backups() {
    shard GET "/project/$SHARDCLOUD_APP_ID/backups"
}

make_room_for_a_backup() {
    # Deletes the oldest finished backups until one more fits. ShardCloud refuses to delete
    # a backup younger than its minimum retention: then the deploy stops and says so.
    local count oldest
    count="$(backups | json 'len(d.get("backups") or [])')"
    while ((count >= max_backups)); do
        oldest="$(backups | json 'sorted([b for b in d["backups"] if b.get("done")], key=lambda b: b["created"])[0]["id"]')"
        echo "The app holds $count backups; deleting the oldest, $oldest."
        if ! shard DELETE "/project/$SHARDCLOUD_APP_ID/backups/$oldest" >/dev/null; then
            echo "::error::Could not delete backup $oldest to make room; delete one in ShardCloud." >&2
            exit 1
        fi
        count=$((count - 1))
    done
}

backup_done() {
    [[ "$(backups | json 'any(b["id"] == a[0] and b.get("done") for b in d.get("backups") or [])' "$1")" == "True" ]]
}

image_rebuilt() {
    # Built, and newer than the build before this deploy: a stale "success" never counts.
    local image status updated
    image="$(shard GET "/custom-images/$SHARDCLOUD_IMAGE_ID")"
    status="$(json 'd.get("status", "")' <<<"$image")"
    updated="$(json 'd.get("updated_at", "")' <<<"$image")"
    echo "Image build: $status (updated $updated)"
    if [[ "$status" == "failed" ]]; then
        echo "::error::ShardCloud could not build the image; see its build logs." >&2
        exit 1
    fi
    [[ "$status" == "success" && "$updated" != "$1" ]]
}

serving_release() {
    local served
    served="$(curl --silent --max-time 10 "$SHARDCLOUD_URL/api/health" | json 'd.get("version", "")' || true)"
    echo "Public health check reports version: ${served:-none}"
    [[ "$served" == "$version" ]]
}

echo "::group::Backup of the app before release $version"
make_room_for_a_backup
backup_id="$(shard POST "/project/$SHARDCLOUD_APP_ID/backups" | json 'd["backup"]["id"]')"
wait_for 1800 "backup $backup_id to finish" backup_done "$backup_id"
echo "Backup $backup_id finished."
echo "::endgroup::"

echo "::group::Rebuild of the image from the release's build context"
previous_build="$(shard GET "/custom-images/$SHARDCLOUD_IMAGE_ID" | json 'd.get("updated_at", "")')"
shard PUT "/custom-images/$SHARDCLOUD_IMAGE_ID" --form "context=@$context_zip" >/dev/null
wait_for 1800 "the image build" image_rebuilt "$previous_build"
echo "::endgroup::"

echo "::group::Restart of the app on the new image"
shard POST "/apps/$SHARDCLOUD_APP_ID/status" \
    --header "Content-Type: application/json" --data '{"status":"restart"}' >/dev/null
wait_for 600 "release $version to answer" serving_release
echo "::endgroup::"

echo "Release $version is live at $SHARDCLOUD_URL."

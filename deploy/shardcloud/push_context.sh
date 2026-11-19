#!/bin/bash
# Publishes one release's build context to the ShardCloud deploy repository (decision
# 3.28 of docs/00). ShardCloud's image is linked to that repository and rebuilds on every
# push, so nothing here calls ShardCloud: its API answers automated clients with a
# Cloudflare challenge.
#
# Usage: deploy/shardcloud/push_context.sh <context directory> <version>
# Environment:
#   SHARDCLOUD_DEPLOY_REMOTE  the repository to push to (git URL);
#   SHARDCLOUD_DEPLOY_KEY     optional: an SSH private key with write access to that
#                             repository only (a GitHub deploy key); github.com's host key
#                             is pinned below, never accepted on first sight.
# The repository's main branch holds the context alone, Dockerfile at its root; each
# release replaces it whole, in one commit named after the version.
set -euo pipefail

context="$1"
version="$2"
: "${SHARDCLOUD_DEPLOY_REMOTE:?}"
[[ -f "$context/Dockerfile" ]] || { echo "::error::$context has no Dockerfile at its root." >&2; exit 1; }

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

if [[ -n "${SHARDCLOUD_DEPLOY_KEY:-}" ]]; then
    # github.com's published ed25519 host key (docs.github.com, "GitHub's SSH key fingerprints").
    printf '%s\n' "github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl" \
        >"$work/known_hosts"
    (umask 077 && printf '%s\n' "$SHARDCLOUD_DEPLOY_KEY" >"$work/key")
    export GIT_SSH_COMMAND="ssh -i $work/key -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes -o UserKnownHostsFile=$work/known_hosts"
fi

git clone --quiet --depth 1 "$SHARDCLOUD_DEPLOY_REMOTE" "$work/repository" 2>/dev/null ||
    git init --quiet --initial-branch main "$work/repository"
cd "$work/repository"
git checkout --quiet -B main
# The context replaces everything but git's own directory.
find . -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
cp -a "$context/." .
git add --all
git -c user.name="sextante release" -c user.email="release@sextante.invalid" \
    commit --quiet --allow-empty -m "Release $version"
git push --quiet origin main
echo "Release $version pushed to the deploy repository; ShardCloud rebuilds the image."

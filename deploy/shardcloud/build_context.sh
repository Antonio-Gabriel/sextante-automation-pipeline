#!/bin/sh
# Assembles the build context of the ShardCloud image from git, not from the working
# tree: only committed files enter, never .env, databases, uploads or node_modules.
# Usage: deploy/shardcloud/build_context.sh <output directory> [git revision] [version]
#   git revision defaults to HEAD; version (X.Y.Z) defaults to "dev".
# The directory keeps the repository layout, with the Dockerfile at its root, as
# ShardCloud requires of a build context. ShardCloud builds a zip without build
# arguments, so the version is written into the Dockerfile itself.
set -eu
out="$1"
revision="${2:-HEAD}"
version="${3:-dev}"
case "$version" in
    *[!0-9A-Za-z.+-]* | "") echo "Invalid version: $version" >&2; exit 1 ;;
esac
root="$(git rev-parse --show-toplevel)"
rm -rf "$out"
mkdir -p "$out"
git -C "$root" archive "$revision" \
    backend/requirements.lock backend/src backend/migrations \
    frontend/package.json frontend/package-lock.json frontend/index.html \
    frontend/tsconfig.json frontend/vite.config.ts frontend/vitest.setup.ts \
    frontend/openapi.json frontend/src frontend/nginx/security-headers.conf \
    sources/catalog.xlsx config/entity_denylist.yaml \
    deploy/shardcloud/nginx.conf deploy/shardcloud/entrypoint.sh deploy/shardcloud/Dockerfile \
    | tar -x -C "$out"
sed "s/^ARG SEXTANTE_RELEASE_VERSION=dev\$/ARG SEXTANTE_RELEASE_VERSION=$version/" \
    "$out/deploy/shardcloud/Dockerfile" >"$out/Dockerfile"
grep -q "^ARG SEXTANTE_RELEASE_VERSION=$version\$" "$out/Dockerfile"

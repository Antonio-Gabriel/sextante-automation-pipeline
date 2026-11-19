#!/bin/sh
# Assembles the build context of the ShardCloud image from git, not from the working
# tree: only committed files enter, never .env, databases, uploads or node_modules.
# Usage: deploy/shardcloud/build_context.sh <output directory> [git revision, default HEAD]
# The directory keeps the repository layout, with the Dockerfile at its root, as
# ShardCloud requires of a build context.
set -eu
out="$1"
revision="${2:-HEAD}"
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
cp "$out/deploy/shardcloud/Dockerfile" "$out/Dockerfile"

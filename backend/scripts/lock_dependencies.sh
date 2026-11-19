#!/bin/sh
# Pins every runtime dependency of pyproject.toml by version and hash in requirements.lock,
# for the container image (SEC-20). pip-compile runs in a throwaway container of the
# image's own base, so the hashes are those of the platform the image installs on.
# Usage: make lock (from backend/), after changing the dependencies of pyproject.toml.
set -eu
image="$1"
docker run --rm -v "$PWD":/project -w /tmp "$image" sh -c "
  pip install --quiet pip-tools==7.7.0 &&
  cp /project/pyproject.toml . && cp -r /project/src . &&
  pip-compile --quiet --generate-hashes --strip-extras --no-header \
    --output-file /project/requirements.lock pyproject.toml &&
  chown $(id -u):$(id -g) /project/requirements.lock"

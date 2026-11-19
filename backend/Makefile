# Backend commands (04-padroes-de-codigo.md §3.1). Run from the backend/ directory.

VENV := .venv
BIN := $(VENV)/bin
ENV_FILE := ../config/.env

.PHONY: install run test test-unit typecheck lint fmt boundaries licenses golden golden-model openapi traceability-matrix check

install:
	python3 -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -e ".[dev]"

# Listens on 127.0.0.1 only: there is no authentication in this version (L-07).
run:
	set -a && . $(ENV_FILE) && set +a && \
	$(BIN)/uvicorn --factory sextante.main:create_app --host 127.0.0.1 --port 8000

test:
	$(BIN)/pytest

test-unit:
	$(BIN)/pytest tests/domain

typecheck:
	$(BIN)/mypy src tests

lint:
	$(BIN)/ruff check src tests scripts migrations
	$(BIN)/ruff format --check src tests scripts migrations

fmt:
	$(BIN)/ruff format src tests scripts
	$(BIN)/ruff check --fix src tests scripts

boundaries:
	$(BIN)/lint-imports

licenses:
	$(BIN)/pip-licenses --partial-match --allow-only="MIT;BSD;Apache;ISC;PSF;Python Software Foundation;Mozilla Public License 2.0;MPL-2.0;Unlicense;CC0" --ignore-packages sextante

# Reads config/.env when present; SEXTANTE_GOLDEN_SAMPLES_PATH points at the local samples.
golden:
	if [ -f $(ENV_FILE) ]; then set -a && . $(ENV_FILE) && set +a; fi && \
	$(BIN)/python -m tests.golden.runner

# MANUAL ONLY: calls the Anthropic API and costs money. Never part of test or check.
golden-model:
	if [ -f $(ENV_FILE) ]; then set -a && . $(ENV_FILE) && set +a; fi && \
	$(BIN)/python -m tests.golden.model_run

# Rewrites frontend/openapi.json from the running contract; then `npm run api:types`.
openapi:
	OPENAPI_SNAPSHOT_WRITE=1 $(BIN)/pytest -q tests/api/test_openapi_contract.py

traceability-matrix:
	$(BIN)/python scripts/traceability_matrix.py

check: lint typecheck boundaries test traceability-matrix

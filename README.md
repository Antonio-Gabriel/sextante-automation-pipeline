# Sextante

Automatic coding of supplier invoice lines for AMT, Advanced Maritime Transports - Transitarios Limitada.

For each line of a supplier invoice, Sextante assigns the exact item number from the catalog, computes a confidence rating, and flags for human review any line where the decision is not safe.

**Status:** under construction. This version delivers tickets 01 to 14 of `.scratch/nucleo-codificacao/`:

- application startup with a validated catalog;
- upload of invoices into a background job;
- reading native PDF invoices in the layout of the samples. A scanned PDF is refused as `pdf_without_text_layer`, and a document that is not an invoice of that layout as `unsupported_document_type`. XLSX invoices are not read in this version;
- an entity check with no language model: MATCH codes against OUTLAYS, NO_MATCH against OUTLAYSP, and an ambiguous entity is left for a reviewer;
- a computed confidence (`HIGH`, `MEDIUM`, `LOW`), the `O00999` fallback in OUTLAYSP only, and review flags;
- line types: a line made only of VAT or discount wording is recorded without code, and only services reach the model;
- the coded results, read back through the API, and exported as CSV or XLSX with the nine columns of the brief;
- review of coded lines, entity resolution and possible duplicates;
- the item choice by Claude, with the approved prompt `item-choice-v2` (ticket 11), whose catalog candidate list is sent as a cached block, read at a tenth of the input price by the calls that follow. The model is `SEXTANTE_MODEL_ID`, `claude-sonnet-5-5` by default; it answers only an index of the target sheet's list, or none, and the server validates it.

## Requirements

- Python 3.12
- The catalog file, `sources/catalog.xlsx`, in the repository. It is the catalog received from AMT, with its file metadata (author and a local Windows path) removed and its data unchanged.

## Install and run

```bash
cp config/.env.example config/.env   # then fill in the real values
cd backend
make install
make run
```

`make run` starts the server on `http://127.0.0.1:8000`. The server listens on the local machine only: the API key closes the API to whoever does not hold it, but there are no per-person accounts (gap L-07). Check that it is up:

```bash
curl http://127.0.0.1:8000/api/health
```

The response gives the SHA-256 of the loaded catalog.

Every `/api` call except the health check needs the `X-API-Key` header, with the value of `SEXTANTE_API_KEY`; without it the answer is 401. The interactive API documentation (Swagger UI) is at `http://127.0.0.1:8000/docs`: press **Authorize** and paste the key once. Every `POST` and `PATCH` except the upload needs an `Idempotency-Key` header: in Swagger, fill the field with any new value, for example `test-1`, and change it for each new request. Without `SEXTANTE_ANTHROPIC_API_KEY` set to a valid key with credit, an invoice with service lines ends `failed`, and can be reprocessed later.

| Endpoint | What it does |
|---|---|
| `POST /api/invoices` | Upload PDF or XLSX invoices (multipart field `files`). Answers at once with a job id |
| `GET /api/jobs/{job_id}` | Job status, invoices counted by status and in total, and the tokens spent, per invoice and in total |
| `POST /api/invoices/{invoice_id}/reprocess` | Code a failed or an already coded invoice again, from its stored text, without a new upload. The earlier coding is kept as superseded, and a line a reviewer had decided goes back to review. Needs `Idempotency-Key` |
| `GET /api/jobs/{job_id}/results` | Coded lines in document order, with the reviewed values in force, paginated (`limit` up to 100, `offset`). Filters: `confidence`, `target_sheet`, `flagged`, `invoice_id` |
| `POST /api/invoices/{invoice_id}/entity-resolution` | Resolve an ambiguous entity as `MATCH` or `NO_MATCH`, with a mandatory note; the invoice is coded again from its stored text. Needs `Idempotency-Key` |
| `GET /api/invoices/{invoice_id}/lines/{line_id}/history` | Every coding of the line, newest first, in force or superseded, with its prompt version, model, catalog digest and the review a person made of it |
| `GET /api/invoices/{invoice_id}/lines/{line_id}/candidates` | Every item of the line's target sheet, best lexical score first, with the model's choice marked |
| `PATCH /api/encoded-lines/{encoded_line_id}` | Correct the code with an item of the line's target sheet, with an optional note. Needs `Idempotency-Key` |
| `POST /api/encoded-lines/{encoded_line_id}/accept` | Accept a pending line without changing its code. Needs `Idempotency-Key` |
| `GET /api/exports/{job_id}?format=csv` | Export with the nine columns: CSV in UTF-8 with BOM, or `format=xlsx` |

The application refuses to start, with a message naming the problem, in either of these cases:

- a variable in `config/.env` is missing;
- the catalog is invalid. A missing sheet, a duplicate or empty item number, a missing `O00999`, or a sheet with more than 100 items all count.

## Rate limits

The API counts requests per time window (SEC-12). Over a quota the answer is `429` with a `Retry-After` header, in seconds. The health check is never limited, a request refused for its API key never uses a quota, and a request refused by one limit is not counted by the others. Quotas belong to the API key: with the single key of this version, everyone using it shares one quota.

| Limit | Default | Variable |
|---|---|---|
| All `/api` calls | 300 per minute | `SEXTANTE_RATE_LIMIT_GENERAL_PER_MINUTE` |
| Upload | 10 per minute | `SEXTANTE_RATE_LIMIT_UPLOAD_PER_MINUTE` |
| Reprocessing and entity resolution | 20 per hour | `SEXTANTE_RATE_LIMIT_REPROCESS_PER_HOUR` |
| Export | 30 per hour | `SEXTANTE_RATE_LIMIT_EXPORT_PER_HOUR` |
| Line correction and acceptance | 120 per minute | `SEXTANTE_RATE_LIMIT_CORRECTION_PER_MINUTE` |

Windows are fixed, so up to twice a quota can pass across the boundary between two windows. The counters live in the memory of the server process. With one process that is enough. With two or more instances each one allows the full quota: running more than one instance needs a shared counter, such as Redis or Valkey.

## Model call ceiling

The worker makes at most `SEXTANTE_MODEL_CALL_CEILING` model calls per `SEXTANTE_MODEL_CALL_WINDOW_SECONDS` (SEC-12). The default is 200 calls per hour, provisional until the real volume is known. Every call counts, retries included, because every attempt is paid. Invoices over the ceiling are never refused nor failed: they stay `queued`, the job shows `waiting_model`, and the worker codes them when the window opens again. The log records `model_call_ceiling_reached`, with the job and the seconds to wait, and `model_call_ceiling_released`.

To code faster, raise the ceiling; to spend less per hour, lower it. Both values must be at least 1. Like the rate limits, the count lives in the memory of the process: two workers would each allow the full ceiling.

## Golden set

The sample invoices never enter the repository. Point `SEXTANTE_GOLDEN_SAMPLES_PATH`, in `config/.env`, at the local folder that holds them, then run `make golden` from `backend/`. It measures, for each sample, the refusal, the entity, the target sheet, the number and types of lines, and which fields the extraction did not find. Each sample is reported as `ok` or with the fields that diverge; the report holds no text from any sample.

The expected results in `backend/tests/golden/expected_results.yaml` are a **proposal still to be confirmed by AMT** (gap L-02). Lines are named by position, never by description. Until AMT confirms them, the thresholds below stay provisional and no accuracy figure is published.

Item codes are not measured by `make golden`, which never calls the model. `make golden-model` measures them with the real model: it codes the samples as the application does and reports, per line, the expected and the assigned item number, the confidence, the lines flagged for review and the tokens spent. It calls the Anthropic API and costs money, so it is run on purpose only, and is never part of `make test` nor of continuous integration. It also needs `SEXTANTE_CATALOG_PATH` and `SEXTANTE_ANTHROPIC_API_KEY`.

## Provisional thresholds

There is no confirmed golden set yet (gap L-02), so every threshold below is provisional and no accuracy figure is published (REQ-CNF-005).

| Threshold | Value | Where | Effect |
|---|---|---|---|
| Entity similarity, low | 60 | `matching/domain/entity_check.py` | Below it, a name that is not AMT's is `NO_MATCH`; at or above it, `AMBIGUOUS` |
| Item score for `HIGH` | 85 | `matching/domain/line_decision.py` | The chosen item must be the lexical top, with a score above this value |
| Margin to the second item | 10 | `matching/domain/line_decision.py` | For `HIGH` the gap must be above this value; at or below it, the two leaders are flagged as conflicting |

The entity threshold was measured on the 12 samples: third parties score below 40, names close to AMT's score above 70.

## Development commands

Run from `backend/`.

| Command | What it does |
|---|---|
| `make test` | Whole test suite. No test calls the Anthropic API |
| `make typecheck` | `mypy --strict` |
| `make lint` | `ruff` lint and format check |
| `make boundaries` | Layer boundaries, with `import-linter` |
| `make licenses` | Dependency licences against the allow-list of NFR-LIC-001 |
| `make traceability-matrix` | Tests cited by requirement. Fails on an unknown identifier |
| `make golden-model` | Manual only: item codes measured with the real model on the local samples. Calls the Anthropic API and costs money |
| `make golden` | Golden set on the local samples, without the model: extraction, entity, target sheet, line types and refusals. Needs `SEXTANTE_GOLDEN_SAMPLES_PATH` |

## Documentation

- `docs/`: decisions and gaps, requirements, architecture, security, coding standards.
- `GLOSSARY.md`: domain vocabulary.
- `OPEN-ITEMS.md`: questions still waiting for an answer.
- `.scratch/nucleo-codificacao/`: the spec and its tickets.

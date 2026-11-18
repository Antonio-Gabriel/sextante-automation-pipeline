# Sextante

Automatic coding of supplier invoice lines for AMT, Advanced Maritime Transports - Transitarios Limitada.

For each line of a supplier invoice, Sextante assigns the exact item number from the catalog, computes a confidence rating, and flags for human review any line where the decision is not safe.

**Status:** under construction. This version delivers tickets 01 and 02 of `.scratch/nucleo-codificacao/`:

- application startup with a validated catalog;
- upload of invoices into a background job, with coding against OUTLAYS;
- the coded results, read back through the API.

Two parts are not wired yet. Until they are, an uploaded invoice is refused with the reason `extractor_not_configured` and is never coded.

- **Reading real PDF invoices:** ticket 12.
- **Calling the Claude model:** ticket 11.

## Requirements

- Python 3.12
- The catalog file, `catalog.xlsx`. It is not in the repository: place it in `sources/`.

## Install and run

```bash
cp config/.env.example config/.env   # then fill in the real values
cd backend
make install
make run
```

`make run` starts the server on `http://127.0.0.1:8000`. The server listens on the local machine only, because this version has no authentication (gap L-07). Check that it is up:

```bash
curl http://127.0.0.1:8000/api/health
```

The response gives the SHA-256 of the loaded catalog.

| Endpoint | What it does |
|---|---|
| `POST /api/invoices` | Upload PDF or XLSX invoices (multipart field `files`). Answers at once with a job id |
| `GET /api/jobs/{job_id}` | Job status, with its invoices counted by status |
| `GET /api/jobs/{job_id}/results` | Coded lines in document order, paginated (`limit` up to 100, `offset`) |

The application refuses to start, with a message naming the problem, in either of these cases:

- a variable in `config/.env` is missing;
- the catalog is invalid. A missing sheet, a duplicate or empty item number, a missing `O00999`, or a sheet with more than 100 items all count.

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
| `make golden` | Golden set. Not implemented yet (ticket 13) |

## Documentation

- `docs/`: decisions and gaps, requirements, architecture, security, coding standards.
- `GLOSSARY.md`: domain vocabulary.
- `OPEN-ITEMS.md`: questions still waiting for an answer.
- `.scratch/nucleo-codificacao/`: the spec and its tickets.

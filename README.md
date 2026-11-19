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
- Node.js 22 and npm, for the frontend
- The catalog file, `sources/catalog.xlsx`, in the repository. It is the catalog received from AMT, with its file metadata (author and a local Windows path) removed and its data unchanged.

## Install and run

There are two ways, side by side. Both read `config/.env`, so create it first:

```bash
cp config/.env.example config/.env   # then fill in the real values
```

| | Without Docker | With Docker |
|---|---|---|
| Needs | Python 3.12 (and Node.js 22 for the frontend) | Docker with Compose v2 |
| API | `cd backend && make install && make run` | `docker compose up --build` |
| Frontend | `cd frontend && npm ci && npm run dev` | started by the same command |
| Address for people | `http://127.0.0.1:5173` | `http://127.0.0.1:8080` |
| API address | `http://127.0.0.1:8000` | `http://127.0.0.1:8000` |
| Data | `backend/sextante.db` and `backend/uploads/` | the `sextante-data` volume |

### Without Docker

```bash
cd backend
make install
make run
```

`make run` starts the server on `http://127.0.0.1:8000`. The server listens on the local machine only: the API key closes the API to whoever does not hold it, but there are no per-person accounts (gap L-07). Check that it is up:

```bash
curl http://127.0.0.1:8000/api/health
```

The response gives the SHA-256 of the loaded catalog.

### With Docker

```bash
docker compose up --build
```

This starts two containers: the API, and the frontend served by nginx. Open `http://127.0.0.1:8080` and sign in with the access token of `config/.env`; nginx forwards `/api` to the API on the same address, so the session cookie works and there is no CORS. To start the API alone, for programs: `docker compose up --build api`.

The API image is built from `backend/Dockerfile` on an official Python base pinned by digest. It runs as an unprivileged user, with a read-only file system except the data volume and a private `/tmp`, and with no Linux capabilities. Settings and secrets come from `config/.env` when the container starts; none is built into the image. Inside the container the paths are fixed by `compose.yaml`: the database and the uploaded invoices live in the named volume `sextante-data`, so they survive restarts, `docker compose down` and rebuilds; the catalog (`sources/catalog.xlsx`) and the denylist (`config/entity_denylist.yaml`) are mounted read-only. The port is published on `127.0.0.1` only. Inside its container the server listens on every interface of the container, because there a process bound to `127.0.0.1` would receive nothing from the published port; this is the one exception to the 127.0.0.1 rule (decision 3.26 of `docs/00`). Check it as above, with `curl http://127.0.0.1:8000/api/health`; the container also reports its own health (`docker compose ps`).

The frontend image compiles the pages in a Node.js stage and serves them with the official unprivileged nginx image (slim variant), pinned by digest. It holds no secret: only `VITE_SEXTANTE_` variables can reach the compiled code, and none is set. nginx sends the security headers of SEC-11 (content security policy, frame and type protections, referrer and permissions policies) on every answer, hides its version, and forwards uploads of up to 50 files of 25 MiB.

The API's dependencies install from `backend/requirements.lock`, pinned by version and hash. After changing the dependencies of `pyproject.toml`, run `make lock` in `backend/` (it needs Docker) and commit the new lock.

`config/.env` is read by the shell in `make run` and by Docker Compose, which is not a shell: keep values free of `$`, backticks and `#`, and put values with spaces in double quotes, so both read them alike.

Stop with `docker compose down`. `docker compose down -v` also **deletes the volume**, with the database and the uploaded invoices. A container and `make run` both use port 8000: run one at a time. If the port is taken, `docker compose up` stops with `address already in use`; stop the other server and run it again. When a page says it could not be loaded, check `docker compose ps` and `docker compose logs api`. Sessions live in the API's memory, so restarting its container signs everyone out; the data stay.

Every `/api` call except the health check and login needs a credential: the `X-API-Key` header, with the value of `SEXTANTE_API_KEY`, for programs and Swagger; or the session cookie of the frontend, for people (see [Frontend](#frontend)). Without either the answer is 401. The interactive API documentation (Swagger UI) is at `http://127.0.0.1:8000/docs`: press **Authorize** and paste the key once. Every `POST`, `PATCH` and `DELETE` except the upload needs an `Idempotency-Key` header: in Swagger, fill the field with any new value, for example `test-1`, and change it for each new request. Without `SEXTANTE_ANTHROPIC_API_KEY` set to a valid key with credit, an invoice with service lines ends `failed`, and can be reprocessed later.

| Endpoint | What it does |
|---|---|
| `POST /api/invoices` | Upload PDF or XLSX invoices (multipart field `files`). Answers at once with a job id |
| `GET /api/invoices/{invoice_id}` | One invoice: extracted header, entity verdict and reason, resolution, target sheet, status, earlier invoice when a possible duplicate, and whether it can be resolved |
| `GET /api/jobs` | Jobs not deleted, newest first: upload date, status, invoices by status and in total. Paginated (`limit` up to 100, `offset`). No file names |
| `DELETE /api/jobs/{job_id}` | Delete a completed or failed job, softly: it leaves every read and action, its records stay. Uploading one of its files again restores it, with its reviews (`restored_job_ids` in the upload answer). A queued or running job is refused with 409. Needs `Idempotency-Key` |
| `GET /api/jobs/{job_id}` | Job status, invoices counted by status and in total, and the tokens spent, per invoice and in total |
| `POST /api/invoices/{invoice_id}/reprocess` | Code a failed or an already coded invoice again, from its stored text, without a new upload. The earlier coding is kept as superseded, and a line a reviewer had decided goes back to review. Needs `Idempotency-Key` |
| `GET /api/jobs/{job_id}/results` | Coded lines in document order, with the reviewed values in force, paginated (`limit` up to 100, `offset`). Filters: `confidence`, `target_sheet`, `flagged`, `invoice_id` |
| `POST /api/invoices/{invoice_id}/entity-resolution` | Resolve an ambiguous entity as `MATCH` or `NO_MATCH`, with a mandatory note; the invoice is coded again from its stored text. Needs `Idempotency-Key` |
| `GET /api/invoices/{invoice_id}/lines/{line_id}/history` | Every coding of the line, newest first, in force or superseded, with its prompt version, model, catalog digest and the review a person made of it |
| `GET /api/invoices/{invoice_id}/lines/{line_id}/candidates` | Every item of the line's target sheet, best lexical score first, with the model's choice marked |
| `PATCH /api/encoded-lines/{encoded_line_id}` | Correct the code with an item of the line's target sheet, with an optional note. Needs `Idempotency-Key` |
| `POST /api/encoded-lines/{encoded_line_id}/accept` | Accept a pending line without changing its code. Needs `Idempotency-Key` |
| `GET /api/exports/{job_id}?format=csv` | Export with the nine columns: CSV in UTF-8 with BOM, or `format=xlsx` |

## Frontend

The frontend is a React application in `frontend/`. Without Docker it runs as two processes: the backend above, and the Vite development server, which serves the pages and forwards every `/api` request to the backend. The browser sees one origin, so there is no CORS.

1. In `config/.env`, set `SEXTANTE_ACCESS_TOKEN` to a long random value, different from the API key (`python3 -c "import secrets; print(secrets.token_urlsafe(32))"`). Restart the backend after changing it.
2. Start the backend: `cd backend && make run`.
3. In another terminal, install and start the frontend:

   ```bash
   cd frontend
   npm ci
   npm run dev
   ```

4. Open `http://127.0.0.1:5173` and type the access token in the login screen.

The token opens a session kept in a cookie the page cannot read (`HttpOnly`, `SameSite=Strict`, `Secure`), valid for 8 hours by default (`SEXTANTE_SESSION_HOURS`). **Sign out** (Sair) ends it in the server. The browser never receives the API key, and no secret is compiled into the frontend: only variables starting `VITE_SEXTANTE_` can reach it, and none is a secret. Sessions live in the memory of the backend: restarting it logs everyone out. A wrong token is refused, and login attempts are limited to 10 per minute (`SEXTANTE_RATE_LIMIT_LOGIN_PER_MINUTE`), counted together for everyone. The server refuses to start when the token equals the API key.

The backend address defaults to `http://127.0.0.1:8000`; set `SEXTANTE_BACKEND_URL` before `npm run dev` to change it. Browsers accept the `Secure` cookie on `http://127.0.0.1` and `http://localhost`; if yours refuses it, set `SEXTANTE_SESSION_COOKIE_SECURE=false` for local use only.

### Language

The interface is in English by default, and in Portuguese on request: the **English | Português** switch is in the sidebar and on the sign-in screen, and the choice is kept in the browser. The server answers in the same language: the frontend sends `Accept-Language` with each request, and error messages, flags, notes, refusal reasons, catalog descriptions and the export follow it. In English a catalog item shows its Description 2, or its Portuguese description when it has no English one. A program that sends no `Accept-Language` gets English. Codes (`code` fields, flag codes, item numbers) and the nine export column names never change. The screen names below are the English ones, with the Portuguese ones in brackets.

### Screens

The panel follows the AMT identity: the logo in the sidebar and a palette built from its navy (`#00137c`), with green, amber and red kept for states. The sidebar holds the navigation (**Upload invoices** (Carregar facturas), **Jobs** (Trabalhos)), the jobs this browser opened recently (identifiers only, kept in the browser), the server's state, the catalog version and **Sign out** (Sair).

**Upload.** Drag PDF files onto **Upload invoices** (Carregar facturas), or choose them. The chosen files are listed with their size and total; more can be added, one taken out, or all cleared, then **Upload N files** (Carregar N ficheiros) sends them. Below, three notes say what the server does with an upload, and the last five jobs of the server link to their screens. The server checks the files; a refusal (too large, too many, wrong type) shows the server's message, and no job is created. Once accepted, the job screen follows the work, polling less and less often and stopping when the job ends or does not exist: invoices queued, coded, to resolve (ambiguous entity), refused and failed, and the tokens spent. When files had already been uploaded the screen says so: either no new job was created and this is the job where they are (with any other earlier jobs linked), or the new job holds only the new files and the earlier jobs are linked. Opening a job adds it to the recent jobs of the sidebar. **View results** (Ver resultados) opens the results of a finished job. When the upload brought back a deleted job, the screen says so and links it.

**Jobs.** **Jobs** (Trabalhos) lists every job of the server, newest first, 20 per page: the job, when it was uploaded, its status and its invoices by status. A finished job links to its results and can be deleted with the bin; the job screen has **Delete** (Apagar) too. A modal asks for confirmation, says the job leaves every screen while its records stay, and that uploading one of its files again restores it with its reviews. Focus starts on **Cancel** (Cancelar); Escape or a click outside cancels. A deleted job leaves the recent jobs of the sidebar.

**Results.** The results of a job list its coded lines in document order: invoice, detected billed entity, exact entity match, sheet, description, item code, catalog description, confidence, review status, flags and notes (the text the API sends, in the chosen language), and the review note. Filter by confidence, sheet, flagged or not, and invoice (the funnel next to an invoice number). The filters live in the address, so copying it shares the exact view; an invalid filter in an address is ignored and the others kept. Pages follow the server's limit of 100 lines; when an address asks for more, the screen says the page was cut. A whole row opens the review of its line, and so do its description (a link) and the button at the end of the row, which stays in view when the table scrolls sideways: **Review** (Rever) for a pending line, **Open** (Abrir) for the others. An invoice number opens the invoice; the funnel beside it filters by it.

**Line review.** A line's description opens its review: the coding in force (code, confidence, review status, flags, note), every item of the line's target sheet best score first with its rank and the model's choice marked, and the history of every coding of the line, in force or superseded, with its prompt version, model, catalog version and the review made of it. **Accept the line** (Aceitar a linha) is offered to a pending line only. To correct, choose an item in the table and press **Correct to …** (Corrigir para …); only items of the line's sheet are offered, and the server checks it again. The optional note shows how many characters are left. Each action makes its own `Idempotency-Key` before the first send, and its button is disabled while it is sent. A line without a target sheet offers no correction: its invoice's entity has to be resolved first, and the screen links to it.

**Invoice.** An invoice number opens the invoice: the extracted header (supplier, tax number, number, date, currency, status and, for a refused document, why), the billed entity detected, the entity verdict and, when ambiguous, why in Portuguese, the target sheet, its coded lines, and a link to the earlier invoice when it is a possible duplicate. An ambiguous invoice not yet resolved shows the resolution form: choose **It is AMT** (É a AMT) or **It is not AMT** (Não é a AMT) and write the mandatory note (the counter shows what is left); the invoice is coded again. The form makes its `Idempotency-Key` before the first send, so a double click or a retry acts once.

**Export and reprocessing.** The results screen has **Export CSV** (Exportar CSV) and **Export XLSX** (Exportar XLSX): the browser downloads the file the server makes, with the person's session and the name the server gives it; a refusal (for example the export rate limit) shows the server's message and saves nothing. An invoice that failed or was already coded offers **Reprocess the invoice** (Reprocessar a factura). Before anything is sent, the screen asks for confirmation and warns that the existing coding is replaced (it stays in the history) and that lines already reviewed go back to review. The request makes its `Idempotency-Key` before it is sent. A refused, ambiguous or queued invoice is not offered reprocessing; if the server refuses anyway, its message is shown.

The API types of the frontend are generated from the backend's OpenAPI document, never written by hand. After changing the API, run `make openapi` in `backend/`, then `npm run api:types` in `frontend/`; `make test` fails while `frontend/openapi.json` is stale.

The application refuses to start, with a message naming the problem, in either of these cases:

- a variable in `config/.env` is missing;
- the catalog is invalid. A missing sheet, a duplicate or empty item number, a missing `O00999`, or a sheet with more than 100 items all count.

## Continuous integration, releases and ShardCloud

Two GitHub Actions workflows live in `.github/workflows/` (decision 3.27 of `docs/00`).

- **CI** (`ci.yml`) runs on every push and pull request.
  1. It runs the backend gates (lint, types, module boundaries, tests, traceability matrix, licences) and the frontend check.
  2. It runs the SEC-20 audits:
     - `pip-audit` on the locked API dependencies;
     - `bandit` on the API code;
     - `npm audit` on the frontend;
     - `gitleaks` over the whole git history.
  3. It builds the three images and scans them with Trivy. The public ShardCloud image fails the run on any fixable HIGH or CRITICAL vulnerability; the two compose images fail it on any fixable CRITICAL.

  CI uses no secret and never calls the model. The golden set needs the private samples, so it is run locally with `make golden`.
- **Release** (`release.yml`) runs when a tag `vX.Y.Z` is pushed.
  1. It runs CI in full.
  2. It builds the ShardCloud image from the git context and pushes it to the private Docker Hub repository as `X.Y.Z`, then scans it.
  3. It waits for a person to approve the `production` environment.
  4. Once approved, it backs up the ShardCloud app and waits for the backup to finish. ShardCloud keeps up to 10 backups per app, so when the app already holds 10, the oldest is deleted first.
  5. It has ShardCloud rebuild the app's image from the same context, and waits for a build newer than the previous one.
  6. It restarts the app and waits until `https://<app>/api/health` answers `"version": "X.Y.Z"`.

  If the backup fails, nothing else happens. If the build fails, the running version stays.

```bash
git tag v1.0.0 && git push origin v1.0.0   # publishes version 1.0.0
```

### The ShardCloud image

`deploy/shardcloud/Dockerfile` puts the whole application in one container, because ShardCloud runs one container per app. Its documentation serves websites on port 80 over HTTPS, but does not say so for custom images. Confirm the port on the first deploy; if ShardCloud expects another, change the `listen` of `deploy/shardcloud/nginx.conf`.

- **Inside:** nginx on port 80 serves the pages, sends the SEC-11 headers and forwards `/api` to the API on the container's `127.0.0.1:8000`. The API runs as an unprivileged user without capabilities. The catalog and the denylist are inside the image.
- **Turned off:** the interactive API documentation.
- **Version:** shown by the health check and in the sidebar.
- **Data:** the database and the invoices live in `/data` in the container.

`deploy/shardcloud/build_context.sh <dir>` assembles the build context from git, so local files never get in. To try the image on your machine:

```bash
deploy/shardcloud/build_context.sh build/shardcloud
docker build --build-arg SEXTANTE_RELEASE_VERSION=local -t sextante:local build/shardcloud
docker run --rm --env-file config/.env -e SEXTANTE_SESSION_COOKIE_SECURE=false -p 127.0.0.1:8081:80 sextante:local
```

### One-time setup

Do these steps once, by hand.

1. **Docker Hub.** Create a private repository (for example `<user>/sextante`) and an access token with *Read & Write* on it.
2. **ShardCloud image.**
   1. Assemble the context and zip it: `deploy/shardcloud/build_context.sh build/shardcloud && (cd build/shardcloud && zip -qr ../sextante.zip .)`.
   2. In the dashboard, create a Custom Docker Image from `build/sextante.zip`, and note its ID.
3. **ShardCloud app.**
   1. Deploy an app from that image with at least 2048 MB of RAM. PDF reading alone may use up to 512 MiB.
   2. Turn on its web access (subdomain or your domain), and note the app ID and its `https://` address.
   3. Set its environment variables: `SEXTANTE_ANTHROPIC_API_KEY`, `SEXTANTE_API_KEY`, `SEXTANTE_ACCESS_TOKEN`, `SEXTANTE_TARGET_ENTITY_NAME`, `SEXTANTE_TARGET_ENTITY_NIF` and `SEXTANTE_REVIEWER_ID`, plus any optional ones from `config/.env.example`. Do not set the paths: the image sets them.
   4. Create a ShardCloud API token (Dashboard → Settings → API Token).
4. **GitHub**, under Settings → Secrets and variables → Actions:
   - **Secrets:** `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, `SHARD_CLOUD_API_KEY`.
   - **Variables:**
     - `DOCKERHUB_REPOSITORY` (for example `<user>/sextante`);
     - `SHARDCLOUD_APP_ID`;
     - `SHARDCLOUD_IMAGE_ID`;
     - `SHARDCLOUD_URL` (the app's `https://` address, with no trailing slash).
5. **GitHub environment.** Under Settings → Environments, create `production` with *Required reviewers*, so each release waits for a person.

### Before using it with real invoices

The published app is on the internet, protected by one shared access token, with no per-person accounts. Keep the token long, and change it in ShardCloud whenever someone who knew it leaves. Two points need confirming first:

- AMT confirms that supplier invoices may be kept at ShardCloud.
- ShardCloud confirms that files in the container (the SQLite database and the uploaded invoices) survive a redeploy.

The pipeline backs the app up before every deploy, but a backup is not a substitute for knowing.

## Rate limits

The API counts requests per time window (SEC-12). Over a quota the answer is `429` with a `Retry-After` header, in seconds. The health check is never limited, a request refused for its credential never uses a quota, and a request refused by one limit is not counted by the others. The API key and the frontend session stand for one principal, so everyone shares one quota. Login attempts, made before any credential, are counted apart.

| Limit | Default | Variable |
|---|---|---|
| All `/api` calls | 300 per minute | `SEXTANTE_RATE_LIMIT_GENERAL_PER_MINUTE` |
| Upload | 10 per minute | `SEXTANTE_RATE_LIMIT_UPLOAD_PER_MINUTE` |
| Reprocessing and entity resolution | 20 per hour | `SEXTANTE_RATE_LIMIT_REPROCESS_PER_HOUR` |
| Export | 30 per hour | `SEXTANTE_RATE_LIMIT_EXPORT_PER_HOUR` |
| Line correction and acceptance | 120 per minute | `SEXTANTE_RATE_LIMIT_CORRECTION_PER_MINUTE` |
| Login with the access token | 10 per minute | `SEXTANTE_RATE_LIMIT_LOGIN_PER_MINUTE` |

Windows are fixed, so up to twice a quota can pass across the boundary between two windows. The counters live in the memory of the server process. With one process that is enough. With two or more instances each one allows the full quota: running more than one instance needs a shared counter, such as Redis or Valkey.

## PDF extraction limits

Every PDF is read in a separate process, with a memory limit and a time limit (SEC-16). A file built to expand on decompression, or to take long to read, stops at a limit: the document is refused as `unsupported_document_type`, the log records `pdf_extraction_limit_reached` with the limit reached and never the file's content, and the worker goes on with the other invoices. Reading happens off the event loop, so the API keeps answering meanwhile.

| Limit | Default | Variable | Range |
|---|---|---|---|
| Memory per PDF, in MiB | 512 | `SEXTANTE_PDF_EXTRACTION_MEMORY_MIB` | 128 to 8192 |
| Time per PDF, in seconds | 30 | `SEXTANTE_PDF_EXTRACTION_TIMEOUT_SECONDS` | 1 to 600 |

Raise the memory limit if valid invoices are refused with `limit: memory` in the log; raise the time limit if they are refused with `limit: time`. A refusal for a limit shows the same reason as a document of the wrong type, `unsupported_document_type`; the log tells them apart. A child that fails for another reason fails the invoice, and the log records `pdf_extraction_failed` with the error type.

The memory limit is the child process's address space, which only Linux enforces: on Linux, if it cannot be set, the invoice fails rather than being read without it. On macOS or Windows the child logs `pdf_memory_limit_unavailable` and only the time limit applies; run on Linux for the full protection. The child also has a CPU time limit, the time limit plus 5 seconds, so it ends by itself if the server stops while it reads. Children start from a forkserver, which needs a writable temporary directory for its socket.

## Model call ceiling

The worker makes at most `SEXTANTE_MODEL_CALL_CEILING` model calls per `SEXTANTE_MODEL_CALL_WINDOW_SECONDS` (SEC-12). The default is 200 calls per hour, provisional until the real volume is known. Every call counts, retries included, because every attempt is paid. A call over the ceiling waits for the next window: its invoice is never refused nor failed, it stays `queued`, the job shows `waiting_model`, and the invoice is coded when the window opens. An invoice that needs no model call, such as a refused document, never waits. The log records `model_call_ceiling_reached`, with the job and the seconds to wait, and `model_call_ceiling_released`.

If the server stops while a job waits, nothing is lost: at startup the worker queues again every job it had claimed, and codes its invoices still queued. An invoice reprocessed while its job waits is coded again too.

To code faster, raise the ceiling; to spend less per hour, lower it. Both values must be at least 1. Like the rate limits, the count lives in the memory of the process: it starts again at zero after a restart, and two workers would each allow the full ceiling.

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

Backend commands, run from `backend/`:

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
| `make openapi` | Rewrite `frontend/openapi.json` from the API |

Frontend commands, run from `frontend/`:

| Command | What it does |
|---|---|
| `npm run dev` | Development server on `http://127.0.0.1:5173`, forwarding `/api` to the backend |
| `npm test` | Component tests, against a simulated API (MSW). No test reaches a server |
| `npm run typecheck` | TypeScript, strict |
| `npm run lint` | ESLint: no `any`, no `dangerouslySetInnerHTML` |
| `npm run licenses` | Production dependency licences against NFR-LIC-001 |
| `npm run api:types` | Generate the API types from `openapi.json` |
| `npm run build` | Production build in `dist/` |
| `npm run check` | Typecheck, lint, tests and licences |

## Documentation

- `docs/`: decisions and gaps, requirements, architecture, security, coding standards.
- `GLOSSARY.md`: domain vocabulary.
- `OPEN-ITEMS.md`: questions still waiting for an answer.
- `.scratch/nucleo-codificacao/`: the spec and its tickets.

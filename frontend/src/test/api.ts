// Answers of the simulated API, shaped like the server's (ErrorResponse, SessionResponse).
import { http, HttpResponse } from "msw";

import type { components } from "@/shared/api/schema";

export const CATALOG_DIGEST = "3f2a9c0d1e4b5a6f7081928374655647382910abcdefabcdefabcdefabcdef12";

export function refused(code: string, message: string, status = 401) {
  return HttpResponse.json({ code, message, correlation_id: "test-correlation" }, { status });
}

export const credentialRefused = () =>
  refused("errors.auth.credential_invalid", "Sessão terminada ou credencial em falta.");

/** A browser without a session: /api/session refuses until the right token is sent. */
export function apiWithoutSession(rightToken: string) {
  let open = false;
  const calls = { login: 0, logout: 0 };
  const handlers = [
    http.get("/api/health", () =>
      HttpResponse.json({ status: "ok", catalog_digest: CATALOG_DIGEST }),
    ),
    http.get("/api/session", () =>
      open ? HttpResponse.json({ authenticated: true }) : credentialRefused(),
    ),
    http.post("/api/session", async ({ request }) => {
      calls.login += 1;
      const body: unknown = await request.json();
      const token = typeof body === "object" && body !== null ? Reflect.get(body, "token") : null;
      if (token !== rightToken) {
        return refused("errors.auth.access_token_invalid", "Token de acesso inválido.");
      }
      open = true;
      return new HttpResponse(null, { status: 204 });
    }),
    http.post("/api/session/end", () => {
      calls.logout += 1;
      open = false;
      return new HttpResponse(null, { status: 204 });
    }),
  ];
  return { handlers, calls };
}

/** A browser already holding a session, with the server up and no job yet. */
export function sessionHandlers() {
  return [
    http.get("/api/jobs", () => HttpResponse.json(jobList([]))),
    http.get("/api/session", () => HttpResponse.json({ authenticated: true })),
    http.get("/api/health", () =>
      HttpResponse.json({ status: "ok", catalog_digest: CATALOG_DIGEST }),
    ),
  ];
}

const NO_INVOICES = {} as const;

type JobListEntry = components["schemas"]["JobListEntryResponse"];

/** A job of the list, of the generated type. */
export function jobEntry(jobId: string, status: string, counts: Record<string, number> = NO_INVOICES): JobListEntry {
  return {
    job_id: jobId,
    status,
    created_at: "2026-11-18T09:00:00+00:00",
    finished_at: status === "completed" || status === "failed" ? "2026-11-18T09:01:00+00:00" : null,
    invoice_counts: counts,
    invoice_total: Object.values(counts).reduce((sum, n) => sum + n, 0),
  };
}

/** A page of the list of jobs. */
export function jobList(jobs: JobListEntry[], offset = 0): components["schemas"]["JobListResponse"] {
  return { jobs, limit: 20, offset, limit_truncated: false };
}

/** A job progress answer of the generated type. */
export function jobProgress(
  jobId: string,
  status: string,
  counts: Record<string, number> = NO_INVOICES,
): components["schemas"]["JobProgressResponse"] {
  const total = Object.values(counts).reduce((sum, n) => sum + n, 0);
  return {
    job_id: jobId,
    status,
    invoice_counts: counts,
    invoice_total: total,
    invoice_tokens: {},
    input_tokens: 12500,
    output_tokens: 80,
  };
}

type ResultLine = components["schemas"]["ResultLineResponse"];

/** A result line of the generated type; fields override the defaults. */
export function resultLine(position: number, fields: Partial<ResultLine> = {}): ResultLine {
  return {
    invoice_id: "inv-1",
    invoice_line_id: `line-${position}`,
    invoice_number: "FT 2026/17",
    line_position: position,
    line_description: `Synthetic service ${position}`,
    billed_entity_detected: "Synthetic Billed Entity Lda",
    exact_entity_match: "YES",
    target_sheet: "OUTLAYSP",
    encoded_line_id: `coded-${position}`,
    item_number: "O00004",
    catalog_description: "Synthetic catalog item",
    confidence: "HIGH",
    review_status: "pending",
    review_note: null,
    flags: [],
    notes: [],
    possible_duplicate_of: null,
    ...fields,
  };
}

type Invoice = components["schemas"]["InvoiceResponse"];

/** An invoice of the generated type; fields override the defaults. */
export function invoiceView(fields: Partial<Invoice> = {}): Invoice {
  return {
    invoice_id: "inv-1",
    job_id: "job-0001-aaaa",
    status: "encoded",
    status_reason: null,
    supplier_name: "Fornecedor Sintético Lda",
    supplier_nif: "5419990001",
    invoice_number: "FT 2026/17",
    invoice_date: "2026-01-12",
    currency: "AOA",
    billed_entity_detected: "Synthetic Billed Entity Lda",
    entity_verdict: "MATCH",
    entity_reason: null,
    entity_resolution: null,
    resolvable: false,
    target_sheet: "OUTLAYS",
    possible_duplicate_of: null,
    ...fields,
  };
}

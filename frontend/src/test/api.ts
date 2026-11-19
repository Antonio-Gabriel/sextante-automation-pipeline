// Answers of the simulated API, shaped like the server's (ErrorResponse, SessionResponse).
import { http, HttpResponse } from "msw";

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

/** A browser already holding a session, with the server up. */
export function sessionHandlers() {
  return [
    http.get("/api/session", () => HttpResponse.json({ authenticated: true })),
    http.get("/api/health", () =>
      HttpResponse.json({ status: "ok", catalog_digest: CATALOG_DIGEST }),
    ),
  ];
}

const NO_INVOICES = {} as const;

/** A job progress answer, shaped like JobProgressResponse. */
export function jobProgress(
  jobId: string,
  status: string,
  counts: Record<string, number> = NO_INVOICES,
) {
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

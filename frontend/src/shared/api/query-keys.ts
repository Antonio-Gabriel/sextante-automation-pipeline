// Structured cache keys, in one place (§8.5). The generated hooks key each query as
// [method, path, init]; a prefix of that key names every query of one resource, which
// is what a mutation invalidates.
export const queryKeys = {
  allJobs: ["get", "/api/jobs/{job_id}"] as const,
  allResults: ["get", "/api/jobs/{job_id}/results"] as const,
  allCandidates: ["get", "/api/invoices/{invoice_id}/lines/{invoice_line_id}/candidates"] as const,
  allHistories: ["get", "/api/invoices/{invoice_id}/lines/{invoice_line_id}/history"] as const,
  allInvoices: ["get", "/api/invoices/{invoice_id}"] as const,
} as const;

// Structured cache keys, in one place (§8.5). The generated hooks key each query as
// [method, path, init]; a prefix of that key names every query of one resource, which
// is what a mutation invalidates.
export const queryKeys = {
  allJobs: ["get", "/api/jobs/{job_id}"] as const,
  // Every page of the list of jobs.
  jobList: ["get", "/api/jobs"] as const,
  allResults: ["get", "/api/jobs/{job_id}/results"] as const,
  allCandidates: ["get", "/api/invoices/{invoice_id}/lines/{invoice_line_id}/candidates"] as const,
  allHistories: ["get", "/api/invoices/{invoice_id}/lines/{invoice_line_id}/history"] as const,
  allInvoices: ["get", "/api/invoices/{invoice_id}"] as const,
  // One line found among its invoice's results, page by page.
  allInvoiceLines: ["invoice-line"] as const,
  invoiceLine: (invoiceId: string, lineId: string) => ["invoice-line", invoiceId, lineId] as const,
} as const;

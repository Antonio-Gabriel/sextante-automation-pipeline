import { useInvoice } from "@/entities/invoice/use-invoice";
import { useResults } from "@/entities/result/use-results";
import { $api } from "@/shared/api/client";
import { isNotFound } from "@/shared/api/errors";

/**
 * Everything the review of one line shows: the invoice, the line's coding in force,
 * every item of its target sheet with scores, and its coding history.
 *
 * Example:
 *   const review = useLineReview(invoiceId, lineId);
 */
export function useLineReview(invoiceId: string, lineId: string) {
  const invoice = useInvoice(invoiceId);
  const jobId = invoice.data?.job_id;
  const results = useResults(jobId ?? "", { invoice: invoiceId }, jobId !== undefined);
  const path = { invoice_id: invoiceId, invoice_line_id: lineId };
  const candidates = $api.useQuery("get", "/api/invoices/{invoice_id}/lines/{invoice_line_id}/candidates", {
    params: { path },
  });
  const history = $api.useQuery("get", "/api/invoices/{invoice_id}/lines/{invoice_line_id}/history", {
    params: { path },
  });
  return {
    invoice: invoice.data,
    line: results.data?.lines.find((line) => line.invoice_line_id === lineId),
    targetSheet: candidates.data?.target_sheet ?? null,
    candidates: candidates.data?.candidates ?? [],
    history: history.data ?? [],
    isPending: invoice.isPending || results.isPending || candidates.isPending,
    notFound: isNotFound(invoice.error) || isNotFound(candidates.error),
  };
}

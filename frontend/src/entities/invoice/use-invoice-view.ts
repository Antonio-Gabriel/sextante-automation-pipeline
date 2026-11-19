import { useResults } from "@/entities/result/use-results";
import { isNotFound } from "@/shared/api/errors";

import { useInvoice } from "./use-invoice";

/**
 * The invoice and its coded lines, read from its job's results with the invoice filter.
 *
 * Example:
 *   const { invoice, lines } = useInvoiceView(invoiceId);
 */
export function useInvoiceView(invoiceId: string) {
  const query = useInvoice(invoiceId);
  const invoice = query.data;
  // The job is known once the invoice is; until then the results wait.
  const results = useResults(invoice?.job_id ?? "", { invoice: invoiceId }, invoice !== undefined);
  return {
    invoice,
    isPending: query.isPending,
    notFound: isNotFound(query.error),
    lines: results.data?.lines ?? [],
  };
}

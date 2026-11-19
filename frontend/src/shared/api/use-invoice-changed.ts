import { useQueryClient } from "@tanstack/react-query";

import { queryKeys } from "./query-keys";

// Every read an invoice's change can touch: the invoice, its job, its lines, their
// results, candidates and history. One list, so a new read is added in one place.
const INVOICE_READS = [
  queryKeys.allInvoices,
  queryKeys.allJobs,
  queryKeys.allResults,
  queryKeys.allInvoiceLines,
  queryKeys.allCandidates,
  queryKeys.allHistories,
];

/**
 * Refresh what an invoice's change touches, after a resolution, review or reprocessing.
 *
 * Example:
 *   const invoiceChanged = useInvoiceChanged();
 *   await invoiceChanged();
 */
export function useInvoiceChanged() {
  const queryClient = useQueryClient();
  return () => Promise.all(INVOICE_READS.map((queryKey) => queryClient.invalidateQueries({ queryKey })));
}

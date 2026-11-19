import { useResults } from "@/entities/result/use-results";
import { pageRange } from "@/entities/result/use-results-view";
import { isNotFound } from "@/shared/api/errors";
import { t } from "@/shared/i18n/t";

import { useInvoice } from "./use-invoice";

/**
 * The invoice, its title, and its coded lines, read from its job's results with the
 * invoice filter; when there are more lines than one page, the screen says so.
 *
 * Example:
 *   const { invoice, title, lines, moreLines } = useInvoiceView(invoiceId);
 */
export function useInvoiceView(invoiceId: string) {
  const query = useInvoice(invoiceId);
  const invoice = query.data;
  // The job is known once the invoice is; until then the results wait.
  const results = useResults(invoice?.job_id ?? "", { invoice: invoiceId }, invoice !== undefined);
  const page = results.data;
  const number = invoice?.invoice_number ?? null;
  return {
    invoice,
    title: number === null ? t("invoice.titleUnknown") : t("invoice.title", { number }),
    isPending: query.isPending,
    notFound: isNotFound(query.error),
    recoding: invoice?.status === "queued",
    lines: page?.lines ?? [],
    moreLines: page !== undefined && pageRange(page).nextOffset !== null,
  };
}

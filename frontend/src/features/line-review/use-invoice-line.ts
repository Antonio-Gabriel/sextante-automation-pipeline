import { useQuery } from "@tanstack/react-query";

import { fetchClient } from "@/shared/api/client";
import { queryKeys } from "@/shared/api/query-keys";

// An invoice has far fewer lines than this; the bound only stops a runaway loop.
const MAX_PAGES = 50;

async function findLine(jobId: string, invoiceId: string, lineId: string) {
  let offset = 0;
  for (let page = 0; page < MAX_PAGES; page += 1) {
    const { data, error } = await fetchClient.GET("/api/jobs/{job_id}/results", {
      params: { path: { job_id: jobId }, query: { invoice_id: invoiceId, offset } },
    });
    if (data === undefined) throw error;
    const line = data.lines.find((candidate) => candidate.invoice_line_id === lineId);
    if (line !== undefined) return line;
    if (data.lines.length < data.limit) return null;
    offset += data.limit;
  }
  return null;
}

/**
 * One line of an invoice, as the results list it, found page by page: an invoice with
 * more lines than one page still finds its last line. Null when the line is not there.
 *
 * Example:
 *   const line = useInvoiceLine(jobId, invoiceId, lineId).data;
 */
export function useInvoiceLine(jobId: string | undefined, invoiceId: string, lineId: string) {
  return useQuery({
    queryKey: queryKeys.invoiceLine(invoiceId, lineId),
    queryFn: () => findLine(jobId ?? "", invoiceId, lineId),
    enabled: jobId !== undefined,
  });
}

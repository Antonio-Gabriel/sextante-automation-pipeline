import { pollingInterval } from "@/entities/job/use-job-progress";
import { $api } from "@/shared/api/client";

/**
 * One invoice: extracted header, entity decision, state and earlier copy. While it is
 * queued, as after a resolution, it is read again with a growing interval (§8.5).
 *
 * Example:
 *   const invoice = useInvoice(invoiceId).data;
 */
export function useInvoice(invoiceId: string) {
  return $api.useQuery(
    "get",
    "/api/invoices/{invoice_id}",
    { params: { path: { invoice_id: invoiceId } } },
    {
      refetchInterval: (query) =>
        query.state.data?.status === "queued" ? pollingInterval(query.state.dataUpdateCount) : false,
    },
  );
}

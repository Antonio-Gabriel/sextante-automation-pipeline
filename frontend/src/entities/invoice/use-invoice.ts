import { useRef } from "react";

import { pollingInterval } from "@/entities/job/use-job-progress";
import { $api } from "@/shared/api/client";

/**
 * One invoice: extracted header, entity decision, state and earlier copy. While it is
 * queued, as after a resolution or reprocessing, it is read again with an interval that
 * grows from the moment it was queued (§8.5).
 *
 * Example:
 *   const invoice = useInvoice(invoiceId).data;
 */
export function useInvoice(invoiceId: string) {
  // Answers seen while queued: the interval restarts each time the invoice is queued.
  const queuedAnswers = useRef(0);
  return $api.useQuery(
    "get",
    "/api/invoices/{invoice_id}",
    { params: { path: { invoice_id: invoiceId } } },
    {
      refetchInterval: (query) => {
        if (query.state.data?.status !== "queued") {
          queuedAnswers.current = 0;
          return false;
        }
        queuedAnswers.current += 1;
        return pollingInterval(queuedAnswers.current - 1);
      },
    },
  );
}

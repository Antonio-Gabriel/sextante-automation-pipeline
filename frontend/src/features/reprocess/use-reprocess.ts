import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { $api } from "@/shared/api/client";
import { errorMessage, isKeyReused } from "@/shared/api/errors";
import { queryKeys } from "@/shared/api/query-keys";
import { useIdempotencyKey } from "@/shared/api/use-idempotency-key";
import { t } from "@/shared/i18n/t";

// The statuses the server reprocesses (NFR-REL-002): a failed or an already coded invoice.
const REPROCESSABLE: ReadonlySet<string> = new Set(["failed", "encoded"]);
const AFFECTED = [queryKeys.allInvoices, queryKeys.allResults, queryKeys.allJobs];

/**
 * Whether the screen offers reprocessing for an invoice in this status.
 *
 * Example:
 *   isReprocessable("rejected") // false
 */
export function isReprocessable(status: string): boolean {
  return REPROCESSABLE.has(status);
}

/**
 * Ask, confirm, then queue the invoice again, once per key (SEC-19).
 *
 * Example:
 *   const reprocess = useReprocess(invoiceId);
 *   reprocess.ask(); reprocess.confirm();
 */
export function useReprocess(invoiceId: string) {
  const queryClient = useQueryClient();
  const idempotency = useIdempotencyKey();
  const [asking, setAsking] = useState(false);
  const refresh = () => Promise.all(AFFECTED.map((queryKey) => queryClient.invalidateQueries({ queryKey })));
  const mutation = $api.useMutation("post", "/api/invoices/{invoice_id}/reprocess", {
    onSuccess: async () => {
      idempotency.renew();
      setAsking(false);
      toast.success(t("reprocess.done"));
      await refresh();
    },
    onError: async (error) => {
      toast.error(errorMessage(error));
      if (isKeyReused(error)) idempotency.renew();
      setAsking(false);
      await refresh();
    },
  });
  return {
    asking,
    isPending: mutation.isPending,
    ask: () => setAsking(true),
    cancel: () => setAsking(false),
    confirm: () =>
      mutation.mutate({
        params: { path: { invoice_id: invoiceId }, header: { "Idempotency-Key": idempotency.key } },
      }),
  };
}

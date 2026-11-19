import { useState } from "react";
import { toast } from "sonner";

import type { InvoiceStatus } from "@/entities/job/job-status";
import { $api } from "@/shared/api/client";
import { errorMessage, isKeyReused } from "@/shared/api/errors";
import { useIdempotencyKey } from "@/shared/api/use-idempotency-key";
import { useInvoiceChanged } from "@/shared/api/use-invoice-changed";
import { t } from "@/shared/i18n/t";

// The statuses the server reprocesses (NFR-REL-002): a failed or an already coded invoice.
const REPROCESSABLE: ReadonlySet<string> = new Set<InvoiceStatus>(["failed", "encoded"]);

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
  const invoiceChanged = useInvoiceChanged();
  const keys = useIdempotencyKey();
  const [confirming, setConfirming] = useState(false);
  const mutation = $api.useMutation("post", "/api/invoices/{invoice_id}/reprocess", {
    onSuccess: async () => {
      keys.renew();
      setConfirming(false);
      toast.success(t("reprocess.done"));
      await invoiceChanged();
    },
    onError: async (error) => {
      toast.error(errorMessage(error));
      if (isKeyReused(error)) keys.renew();
      setConfirming(false);
      await invoiceChanged();
    },
  });
  return {
    confirming,
    isPending: mutation.isPending,
    ask: () => setConfirming(true),
    cancel: () => setConfirming(false),
    confirm: () =>
      mutation.mutate({
        params: { path: { invoice_id: invoiceId }, header: { "Idempotency-Key": keys.keyFor(invoiceId) } },
      }),
  };
}

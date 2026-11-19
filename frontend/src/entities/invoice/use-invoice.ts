import { $api } from "@/shared/api/client";

/**
 * One invoice: extracted header, entity decision, state and earlier copy.
 *
 * Example:
 *   const invoice = useInvoice(invoiceId).data;
 */
export function useInvoice(invoiceId: string) {
  return $api.useQuery("get", "/api/invoices/{invoice_id}", {
    params: { path: { invoice_id: invoiceId } },
  });
}

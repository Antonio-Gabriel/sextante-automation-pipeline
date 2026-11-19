import { useInvoice } from "@/entities/invoice/use-invoice";
import { $api } from "@/shared/api/client";
import { errorMessage, isNotFound } from "@/shared/api/errors";
import type { MessageKey } from "@/shared/i18n/t";

import { useInvoiceLine } from "./use-invoice-line";

export type LineReviewState = "loading" | "notFound" | "failed" | "ready";
/** What the reviewer can do: correct and accept, or nothing until the cause is fixed. */
export type Decision = "noSheet" | "notCoded" | "ready";

const STATE_TEXT: Partial<Record<LineReviewState, MessageKey>> = {
  loading: "review.loading",
  notFound: "review.notFound",
};

/**
 * Everything the review of one line shows, and what the screen should do with it: the
 * invoice, the line, every item of its target sheet with scores, and its history.
 *
 * Example:
 *   const review = useLineReview(invoiceId, lineId);
 */
export function useLineReview(invoiceId: string, lineId: string) {
  const invoice = useInvoice(invoiceId);
  const lineQuery = useInvoiceLine(invoice.data?.job_id, invoiceId, lineId);
  const path = { invoice_id: invoiceId, invoice_line_id: lineId };
  const candidates = $api.useQuery("get", "/api/invoices/{invoice_id}/lines/{invoice_line_id}/candidates", {
    params: { path },
  });
  const history = $api.useQuery("get", "/api/invoices/{invoice_id}/lines/{invoice_line_id}/history", {
    params: { path },
  });
  const queries = [invoice, lineQuery, candidates, history];
  const failed = queries.find((query) => query.isError);
  const line = lineQuery.data ?? undefined;
  const targetSheet = candidates.data?.target_sheet ?? null;
  const state: LineReviewState = queries.some((query) => isNotFound(query.error)) || lineQuery.data === null
    ? "notFound"
    : failed !== undefined
      ? "failed"
      : queries.some((query) => query.isPending)
        ? "loading"
        : "ready";
  const decision: Decision = targetSheet === null ? "noSheet" : line?.encoded_line_id == null ? "notCoded" : "ready";
  return {
    state,
    stateText: STATE_TEXT[state] ?? null,
    failure: failed === undefined ? null : errorMessage(failed.error),
    invoice: invoice.data,
    line,
    targetSheet,
    decision,
    reviewPending: line?.review_status === "pending",
    candidates: candidates.data?.candidates ?? [],
    history: history.data ?? [],
  };
}

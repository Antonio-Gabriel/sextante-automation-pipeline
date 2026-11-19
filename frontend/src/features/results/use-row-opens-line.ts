import { useNavigate } from "@tanstack/react-router";
import type { MouseEvent } from "react";

export const LINE_ROUTE = "/invoices/$invoiceId/lines/$lineId";

/**
 * A click on a result row opens its line review, unless it was on a link or a button of
 * the row, or ended a text selection. The row is a larger target for the pointer;
 * keyboards use the links it holds.
 *
 * Example:
 *   const openFromRow = useRowOpensLine({ invoiceId, lineId });
 *   <tr onClick={openFromRow}>
 */
export function useRowOpensLine(params: { invoiceId: string; lineId: string }) {
  const navigate = useNavigate();
  return (event: MouseEvent<HTMLTableRowElement>) => {
    const target = event.target;
    if (target instanceof Element && target.closest("a, button") !== null) return;
    if (window.getSelection()?.toString()) return;
    void navigate({ to: LINE_ROUTE, params });
  };
}

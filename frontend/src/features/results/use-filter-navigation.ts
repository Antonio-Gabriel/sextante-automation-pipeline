import { useNavigate } from "@tanstack/react-router";

import {
  parseConfidence,
  parseFlagged,
  parseSheet,
  type ResultFilters,
} from "@/entities/result/result-filters";

/**
 * Changes the view by changing the address: a new filter goes back to the first page.
 * Select values are turned into filters here, not in the component (§8.2).
 *
 * Example:
 *   const filters = useFilterNavigation(jobId);
 *   filters.chooseConfidence("LOW");
 */
export function useFilterNavigation(jobId: string) {
  const navigate = useNavigate();
  const go = (search: (previous: ResultFilters) => ResultFilters) =>
    navigate({ to: "/jobs/$jobId/results", params: { jobId }, search });
  const setFilter = (change: Partial<ResultFilters>) =>
    go((previous) => ({ ...previous, ...change, offset: undefined }));
  return {
    chooseConfidence: (value: string) => setFilter({ confidence: parseConfidence(value) }),
    chooseSheet: (value: string) => setFilter({ sheet: parseSheet(value) }),
    chooseFlagged: (value: string) => setFilter({ flagged: parseFlagged(value) }),
    chooseInvoice: (invoiceId: string | undefined) => setFilter({ invoice: invoiceId }),
    setOffset: (offset: number) => go((previous) => ({ ...previous, offset })),
    clear: () => go(() => ({})),
  };
}

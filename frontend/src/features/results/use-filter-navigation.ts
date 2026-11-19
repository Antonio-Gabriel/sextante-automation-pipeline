import { useNavigate } from "@tanstack/react-router";

import type { ResultFilters } from "@/entities/result/result-filters";

/**
 * Changes the view by changing the address: a new filter goes back to the first page.
 *
 * Example:
 *   const { setFilter } = useFilterNavigation(jobId);
 *   setFilter({ confidence: "LOW" });
 */
export function useFilterNavigation(jobId: string) {
  const navigate = useNavigate();
  const go = (search: (previous: ResultFilters) => ResultFilters) =>
    navigate({ to: "/jobs/$jobId/results", params: { jobId }, search });
  return {
    setFilter: (change: Partial<ResultFilters>) =>
      go((previous) => ({ ...previous, ...change, offset: undefined })),
    setOffset: (offset: number) => go((previous) => ({ ...previous, offset })),
    clear: () => go(() => ({})),
  };
}

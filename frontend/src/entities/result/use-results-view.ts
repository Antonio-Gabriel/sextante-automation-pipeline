import type { components } from "@/shared/api/schema";

import type { ResultFilters } from "./result-filters";
import { useResults } from "./use-results";

type ResultsPage = components["schemas"]["ResultsPageResponse"];

export interface PageWindow {
  from: number;
  to: number;
  previousOffset: number | null;
  nextOffset: number | null;
  truncated: boolean;
  serverLimit: number;
}

/**
 * Where this page sits: its line range and the offsets of its neighbours. The server
 * gives no total, so a full page means there may be another.
 *
 * Example:
 *   pageWindow({ lines: [...100], limit: 100, offset: 0, limit_truncated: false })
 *   // { from: 1, to: 100, previousOffset: null, nextOffset: 100, ... }
 */
export function pageWindow(page: ResultsPage): PageWindow {
  const count = page.lines.length;
  return {
    from: count === 0 ? 0 : page.offset + 1,
    to: page.offset + count,
    previousOffset: page.offset > 0 ? Math.max(page.offset - page.limit, 0) : null,
    nextOffset: count === page.limit ? page.offset + page.limit : null,
    truncated: page.limit_truncated,
    serverLimit: page.limit,
  };
}

/**
 * The lines of the page and where the page sits, for the results screen.
 *
 * Example:
 *   const { lines, window } = useResultsView(jobId, filters);
 */
export function useResultsView(jobId: string, filters: ResultFilters) {
  const query = useResults(jobId, filters);
  const page = query.data;
  return {
    isPending: query.isPending,
    lines: page?.lines ?? [],
    window: page === undefined ? null : pageWindow(page),
  };
}

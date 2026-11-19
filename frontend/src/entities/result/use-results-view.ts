import type { components } from "@/shared/api/schema";
import { errorMessage } from "@/shared/api/errors";

import type { ResultFilters } from "./result-filters";
import { useResults } from "./use-results";

type ResultsPage = components["schemas"]["ResultsPageResponse"];

export interface PageRange {
  from: number;
  to: number;
  previousOffset: number | null;
  nextOffset: number | null;
  truncated: boolean;
  serverLimit: number;
}

/**
 * Where this page sits: its line range and the offsets of its neighbours. The server
 * gives no total, so a full page means there may be another; past the end, the page is
 * empty and only "previous" is left.
 *
 * Example:
 *   pageRange({ lines: [...100], limit: 100, offset: 0, limit_truncated: false })
 *   // { from: 1, to: 100, previousOffset: null, nextOffset: 100, ... }
 */
export function pageRange(page: ResultsPage): PageRange {
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

export type ResultsState = "loading" | "failed" | "empty" | "pastEnd" | "lines";

/**
 * The lines of the page, where it sits, and what the screen should say about it.
 *
 * Example:
 *   const { state, lines, range } = useResultsView(jobId, filters);
 */
export function useResultsView(jobId: string, filters: ResultFilters) {
  const query = useResults(jobId, filters);
  const page = query.data;
  const lines = page?.lines ?? [];
  const range = page === undefined ? null : pageRange(page);
  const state: ResultsState = query.isPending
    ? "loading"
    : query.isError
      ? "failed"
      : lines.length > 0
        ? "lines"
        : (filters.offset ?? 0) > 0
          ? "pastEnd"
          : "empty";
  return {
    state,
    lines,
    range,
    failure: query.isError ? errorMessage(query.error) : null,
    // The filtered invoice's number, when its lines are on the page.
    invoiceNumber: filters.invoice === undefined ? null : (lines[0]?.invoice_number ?? null),
  };
}

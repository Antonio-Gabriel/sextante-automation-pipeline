import { ChevronLeft, ChevronRight } from "lucide-react";

import type { PageRange } from "@/entities/result/use-results-view";
import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";

import { useFilterNavigation } from "./use-filter-navigation";

/**
 * The line range of the page and the way to its neighbours.
 *
 * Example:
 *   <ResultsPagination jobId={jobId} range={range} />
 */
export function ResultsPagination({ jobId, range }: { jobId: string; range: PageRange }) {
  const { setOffset } = useFilterNavigation(jobId);
  const { previousOffset, nextOffset } = range;
  return (
    <nav aria-label={t("results.pagination.label")} className="flex items-center justify-between gap-4">
      <p className="text-sm text-slate-500">
        {range.from > 0 && t("results.pagination.range", { from: range.from, to: range.to })}
      </p>
      <div className="flex gap-2">
        <Button variant="outline" size="sm" disabled={previousOffset === null} onClick={() => previousOffset !== null && setOffset(previousOffset)}>
          <ChevronLeft />
          {t("results.pagination.previous")}
        </Button>
        <Button variant="outline" size="sm" disabled={nextOffset === null} onClick={() => nextOffset !== null && setOffset(nextOffset)}>
          {t("results.pagination.next")}
          <ChevronRight />
        </Button>
      </div>
    </nav>
  );
}

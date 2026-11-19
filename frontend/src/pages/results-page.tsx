import { getRouteApi } from "@tanstack/react-router";
import { TriangleAlert } from "lucide-react";

import { shortJobId } from "@/entities/job/job-status";
import { useResultsView } from "@/entities/result/use-results-view";
import { ResultsFilters } from "@/features/results/results-filters";
import { ResultsPagination } from "@/features/results/results-pagination";
import { ResultsTable } from "@/features/results/results-table";
import { Page } from "@/shared/layout/page";
import { t } from "@/shared/i18n/t";

const route = getRouteApi("/_app/jobs/$jobId/results");

/** The coded lines of one job, filtered and paged from the address. */
export function ResultsPage() {
  const { jobId } = route.useParams();
  const filters = route.useSearch();
  const { isPending, lines, window } = useResultsView(jobId, filters);

  return (
    <Page title={t("results.title", { id: shortJobId(jobId) })} description={t("results.description")}>
      <ResultsFilters jobId={jobId} filters={filters} />
      {window?.truncated === true && (
        <p role="status" className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          <TriangleAlert className="size-4" aria-hidden />
          {t("results.truncated", { max: window.serverLimit })}
        </p>
      )}
      {isPending ? (
        <p className="text-sm text-slate-500">{t("results.loading")}</p>
      ) : lines.length === 0 ? (
        <p className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
          {t("results.empty")}
        </p>
      ) : (
        <ResultsTable jobId={jobId} lines={lines} />
      )}
      {window !== null && lines.length > 0 && <ResultsPagination jobId={jobId} window={window} />}
    </Page>
  );
}

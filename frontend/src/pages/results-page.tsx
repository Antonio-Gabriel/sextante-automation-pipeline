import { getRouteApi } from "@tanstack/react-router";
import { TriangleAlert } from "lucide-react";

import { shortJobId } from "@/entities/job/job-status";
import { useResultsView, type ResultsState } from "@/entities/result/use-results-view";
import { ExportButtons } from "@/features/export/export-buttons";
import { ResultsFilters } from "@/features/results/results-filters";
import { ResultsPagination } from "@/features/results/results-pagination";
import { ResultsTable } from "@/features/results/results-table";
import { useFilterNavigation } from "@/features/results/use-filter-navigation";
import { Page } from "@/shared/layout/page";
import { t, type MessageKey } from "@/shared/i18n/t";

const route = getRouteApi("/_app/jobs/$jobId/results");

const EMPTY_TEXT: Partial<Record<ResultsState, MessageKey>> = {
  loading: "results.loading",
  empty: "results.empty",
  pastEnd: "results.noMore",
};

/** The coded lines of one job, filtered and paged from the address. */
export function ResultsPage() {
  const { jobId } = route.useParams();
  const filters = route.useSearch();
  const view = useResultsView(jobId, filters);
  const navigation = useFilterNavigation(jobId);
  const emptyText = EMPTY_TEXT[view.state];

  return (
    <Page
      title={t("results.title", { id: shortJobId(jobId) })}
      description={t("results.description")}
      actions={<ExportButtons jobId={jobId} />}
    >
      <ResultsFilters jobId={jobId} filters={filters} invoiceLabel={view.invoiceNumber} />
      {view.range?.truncated === true && (
        <p role="status" className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          <TriangleAlert className="size-4" aria-hidden />
          {t("results.truncated", { max: view.range.serverLimit })}
        </p>
      )}
      {view.failure !== null && (
        <p role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {view.failure}
        </p>
      )}
      {emptyText !== undefined && (
        <p className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">
          {t(emptyText)}
        </p>
      )}
      {view.state === "lines" && <ResultsTable lines={view.lines} onFilterInvoice={navigation.chooseInvoice} />}
      {view.range !== null && (view.state === "lines" || view.state === "pastEnd") && (
        <ResultsPagination jobId={jobId} range={view.range} />
      )}
    </Page>
  );
}

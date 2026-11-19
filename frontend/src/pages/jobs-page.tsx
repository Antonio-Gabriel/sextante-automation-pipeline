import { getRouteApi, Link } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight, FolderOpen, Upload } from "lucide-react";

import { useJobs } from "@/entities/job/use-jobs";
import { JobsTable } from "@/features/jobs/jobs-table";
import { errorMessage } from "@/shared/api/errors";
import { Page } from "@/shared/layout/page";
import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";

const route = getRouteApi("/_app/jobs");
export const JOBS_PAGE_SIZE = 20;

/** Every job of the server, newest first, paged from the address. */
export function JobsPage() {
  const { offset = 0 } = route.useSearch();
  const navigate = route.useNavigate();
  const query = useJobs(JOBS_PAGE_SIZE, offset);
  const jobs = query.data?.jobs;
  const setOffset = (next: number) => navigate({ search: next === 0 ? {} : { offset: next } });

  return (
    <Page
      title={t("jobs.title")}
      description={t("jobs.description")}
      actions={
        <Button asChild>
          <Link to="/">
            <Upload />
            {t("nav.upload")}
          </Link>
        </Button>
      }
    >
      {query.isPending && <p className="text-sm text-slate-500">{t("jobs.loading")}</p>}
      {query.isError && (
        <p role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {errorMessage(query.error)}
        </p>
      )}
      {jobs !== undefined && jobs.length === 0 && offset === 0 && <NoJobs />}
      {jobs !== undefined && (jobs.length > 0 || offset > 0) && (
        <>
          {jobs.length > 0 ? <JobsTable jobs={jobs} /> : <p className="text-sm text-slate-500">{t("jobs.noMore")}</p>}
          <nav aria-label={t("jobs.pagination")} className="flex justify-end gap-2">
            <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - JOBS_PAGE_SIZE))}>
              <ChevronLeft />
              {t("jobs.previous")}
            </Button>
            <Button variant="outline" size="sm" disabled={jobs.length < JOBS_PAGE_SIZE} onClick={() => setOffset(offset + JOBS_PAGE_SIZE)}>
              {t("jobs.next")}
              <ChevronRight />
            </Button>
          </nav>
        </>
      )}
    </Page>
  );
}

function NoJobs() {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center">
      <span className="flex size-12 items-center justify-center rounded-full bg-brand-50 text-brand-700">
        <FolderOpen className="size-6" aria-hidden />
      </span>
      <p className="font-medium text-slate-900">{t("jobs.empty")}</p>
      <p className="text-sm text-slate-500">{t("jobs.emptyHint")}</p>
    </div>
  );
}

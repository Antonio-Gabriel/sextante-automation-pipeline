import { getRouteApi, Link } from "@tanstack/react-router";
import { ArrowRight, Coins, Files, History, Info } from "lucide-react";

import { JobProgressBar } from "@/entities/job/job-progress-bar";
import { INVOICE_STATUSES, invoiceCount, shortJobId } from "@/entities/job/job-status";
import { alreadyUploadedNotice, useJobView, type AlreadyUploadedNotice } from "@/entities/job/use-job-view";
import { DeleteJobButton } from "@/features/jobs/delete-job-button";
import { formatNumber } from "@/shared/format";
import { Page } from "@/shared/layout/page";
import { t } from "@/shared/i18n/t";
import { Badge } from "@/shared/ui-kit/badge";
import { Button } from "@/shared/ui-kit/button";
import { Stat } from "@/shared/ui-kit/stat";

const route = getRouteApi("/_app/jobs/$jobId");

/** Progress of one job: status, invoices by state, tokens, and the way to its results. */
export function JobPage() {
  const { jobId } = route.useParams();
  const { already, restored } = route.useSearch();
  const navigate = route.useNavigate();
  const view = useJobView(jobId);
  const notice = alreadyUploadedNotice(jobId, already ?? []);

  return (
    <Page
      title={t("job.title", { id: shortJobId(jobId) })}
      breadcrumb={
        <Link to="/jobs" className="text-xs text-slate-500 hover:text-brand-700 hover:underline">
          {t("job.breadcrumb")}
        </Link>
      }
      actions={
        view.job !== undefined && view.finished && (
          <>
            <DeleteJobButton jobId={jobId} look="full" onDeleted={() => navigate({ to: "/jobs" })} />
            <Button asChild>
              <Link to="/jobs/$jobId/results" params={{ jobId }}>
                {t("job.viewResults")}
                <ArrowRight />
              </Link>
            </Button>
          </>
        )
      }
    >
      {restored !== undefined && restored.length > 0 && <Restored jobIds={restored} />}
      {notice !== null && <AlreadyUploaded notice={notice} />}
      {view.notFound && <p className="text-sm text-slate-600">{t("job.notFound")}</p>}
      {view.job !== undefined && (
        <>
          <div aria-live="polite" className="flex items-center gap-3">
            <Badge tone={view.status.tone}>{t(view.status.label)}</Badge>
            <JobProgressBar done={view.done} total={view.total} />
          </div>
          <section className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
            <Stat icon={<Files />} label={t("job.total")} value={view.total} />
            {INVOICE_STATUSES.map(({ status, label }) => (
              <Stat key={status} label={t(label)} value={invoiceCount(view.job, status)} />
            ))}
          </section>
          <Stat
            className="max-w-xs"
            icon={<Coins />}
            label={t("job.tokens")}
            value={t("job.tokenCounts", {
              input: formatNumber(view.job.input_tokens),
              output: formatNumber(view.job.output_tokens),
            })}
          />
        </>
      )}
    </Page>
  );
}

function Restored({ jobIds }: { jobIds: readonly string[] }) {
  return (
    <div role="status" className="flex gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">
      <History className="size-5 shrink-0 text-emerald-700" aria-hidden />
      <div className="flex flex-col gap-1">
        <p>{t("job.restored")}</p>
        <ul className="flex flex-wrap gap-2">
          {jobIds.map((id) => (
            <li key={id}>
              <Link to="/jobs/$jobId" params={{ jobId: id }} className="font-mono text-emerald-800 underline">
                {shortJobId(id)}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function AlreadyUploaded({ notice }: { notice: AlreadyUploadedNotice }) {
  const links = notice.otherJobIds.map((id) => (
    <li key={id}>
      <Link to="/jobs/$jobId" params={{ jobId: id }} className="font-mono text-brand-700 underline">
        {shortJobId(id)}
      </Link>
    </li>
  ));
  return (
    <div role="status" className="flex gap-3 rounded-xl border border-brand-200 bg-brand-50 p-4 text-sm text-brand-900">
      <Info className="size-5 shrink-0 text-brand-700" aria-hidden />
      <div className="flex flex-col gap-1">
        <p>{notice.noNewJob ? t("job.alreadyUploadedHere") : t("job.alreadyUploadedElsewhere")}</p>
        {links.length > 0 && (
          <>
            {notice.noNewJob && <p>{t("job.alreadyUploadedAlsoIn")}</p>}
            <ul className="flex flex-wrap gap-2">{links}</ul>
          </>
        )}
      </div>
    </div>
  );
}

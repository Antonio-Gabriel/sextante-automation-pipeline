import { getRouteApi, Link } from "@tanstack/react-router";
import { ArrowRight, Coins, Files, Info } from "lucide-react";

import { INVOICE_STATUSES, isJobFinished, jobStatusView } from "@/entities/job/job-status";
import { useJobProgress } from "@/entities/job/use-job-progress";
import { Page } from "@/shared/layout/page";
import { t } from "@/shared/i18n/t";
import { Badge } from "@/shared/ui-kit/badge";
import { Button } from "@/shared/ui-kit/button";
import { Stat } from "@/shared/ui-kit/stat";

import { JobProgressBar } from "./job-progress-bar";

const route = getRouteApi("/_app/jobs/$jobId");

export function JobPage() {
  const { jobId } = route.useParams();
  const { already } = route.useSearch();
  const job = useJobProgress(jobId).data;
  const status = job === undefined ? undefined : jobStatusView(job.status);
  const finished = job !== undefined && isJobFinished(job.status);

  return (
    <Page
      title={`${t("job.title")} ${jobId.slice(0, 8)}`}
      breadcrumb={<p className="text-xs text-slate-500">{t("job.breadcrumb")}</p>}
      actions={
        finished && (
          <Button asChild>
            <Link to="/jobs/$jobId/results" params={{ jobId }}>
              {t("job.viewResults")}
              <ArrowRight />
            </Link>
          </Button>
        )
      }
    >
      <AlreadyUploaded jobId={jobId} already={already ?? []} />
      {job !== undefined && status !== undefined && (
        <>
          <div className="flex items-center gap-3">
            <Badge tone={status.tone}>{t(status.label)}</Badge>
            <JobProgressBar counts={job.invoice_counts} total={job.invoice_total} />
          </div>
          <section className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
            <Stat icon={<Files />} label={t("job.total")} value={job.invoice_total} />
            {INVOICE_STATUSES.map(({ status: key, label }) => (
              <Stat key={key} label={t(label)} value={job.invoice_counts[key] ?? 0} />
            ))}
          </section>
          <Stat
            className="max-w-xs"
            icon={<Coins />}
            label={`${t("job.tokens")} (${t("job.tokensDetail")})`}
            value={`${job.input_tokens.toLocaleString("pt-PT")} / ${job.output_tokens.toLocaleString("pt-PT")}`}
          />
        </>
      )}
    </Page>
  );
}

function AlreadyUploaded({ jobId, already }: { jobId: string; already: readonly string[] }) {
  if (already.length === 0) return null;
  const elsewhere = already.filter((id) => id !== jobId);
  return (
    <div role="status" className="flex gap-3 rounded-xl border border-brand-200 bg-brand-50 p-4 text-sm text-brand-900">
      <Info className="size-5 shrink-0 text-brand-700" aria-hidden />
      {elsewhere.length === 0 ? (
        <p>{t("job.alreadyUploadedHere")}</p>
      ) : (
        <div className="flex flex-col gap-1">
          <p>{t("job.alreadyUploadedElsewhere")}</p>
          <ul className="flex flex-wrap gap-2">
            {elsewhere.map((id) => (
              <li key={id}>
                <Link to="/jobs/$jobId" params={{ jobId: id }} className="font-mono text-brand-700 underline">
                  {id.slice(0, 8)}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

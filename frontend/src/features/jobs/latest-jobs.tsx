import { Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";

import { jobStatusView, shortJobId } from "@/entities/job/job-status";
import { useJobs } from "@/entities/job/use-jobs";
import { formatDateTime } from "@/shared/format";
import { t } from "@/shared/i18n/t";
import { Badge } from "@/shared/ui-kit/badge";
import { Card, CardHeader, CardTitle } from "@/shared/ui-kit/card";

const LATEST = 5;

/** The last jobs of the server, to go back to one without searching. Hidden when none. */
export function LatestJobs() {
  const jobs = useJobs(LATEST, 0).data?.jobs ?? [];
  if (jobs.length === 0) return null;
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between pb-3">
        <CardTitle>{t("upload.latest")}</CardTitle>
        <Link to="/jobs" className="flex items-center gap-1 text-sm font-medium text-brand-700 hover:underline [&_svg]:size-4">
          {t("upload.latestAll")}
          <ArrowRight aria-hidden />
        </Link>
      </CardHeader>
      <ul className="divide-y divide-slate-100 border-t border-slate-100">
        {jobs.map((job) => {
          const status = jobStatusView(job.status);
          return (
            <li key={job.job_id}>
              <Link to="/jobs/$jobId" params={{ jobId: job.job_id }} className="flex items-center gap-4 px-5 py-3 text-sm hover:bg-slate-50">
                <span className="font-mono font-medium text-brand-700">{shortJobId(job.job_id)}</span>
                <span className="tabular-nums text-slate-500">{formatDateTime(job.created_at)}</span>
                <span className="flex-1 text-slate-600">{job.invoice_total === 1 ? t("jobs.invoiceTotalOne") : t("jobs.invoiceTotal", { count: job.invoice_total })}</span>
                <Badge tone={status.tone}>{t(status.label)}</Badge>
              </Link>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

import { Link } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";

import { INVOICE_STATUSES, invoiceCount, isJobFinished, jobStatusView, shortJobId } from "@/entities/job/job-status";
import type { JobListEntry } from "@/entities/job/use-jobs";
import { formatDateTime } from "@/shared/format";
import { t, type MessageKey } from "@/shared/i18n/t";
import { Badge } from "@/shared/ui-kit/badge";
import { Button } from "@/shared/ui-kit/button";

import { DeleteJobButton } from "./delete-job-button";

const COLUMNS: readonly MessageKey[] = [
  "jobs.columns.job",
  "jobs.columns.uploadedAt",
  "jobs.columns.status",
  "jobs.columns.invoices",
];

const CELL = "px-4 py-3 align-middle";

/**
 * The jobs of the server, one per row, with the way to their results and their deletion.
 *
 * Example:
 *   <JobsTable jobs={data.jobs} />
 */
export function JobsTable({ jobs }: { jobs: readonly JobListEntry[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-xs">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="border-b border-slate-200 bg-slate-50 text-xs font-medium uppercase tracking-wide text-slate-500">
          <tr>
            {COLUMNS.map((column) => (
              <th key={column} scope="col" className="px-4 py-2.5 font-medium">
                {t(column)}
              </th>
            ))}
            <th scope="col" className="px-4 py-2.5 text-right font-medium">
              <span className="sr-only">{t("jobs.columns.actions")}</span>
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {jobs.map((job) => (
            <JobRow key={job.job_id} job={job} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function JobRow({ job }: { job: JobListEntry }) {
  const status = jobStatusView(job.status);
  const finished = isJobFinished(job.status);
  return (
    <tr className="hover:bg-slate-50">
      <td className={CELL}>
        <Link to="/jobs/$jobId" params={{ jobId: job.job_id }} className="font-mono font-medium text-brand-700 underline decoration-brand-200 underline-offset-2 hover:decoration-brand-700">
          {shortJobId(job.job_id)}
        </Link>
      </td>
      <td className={`${CELL} tabular-nums text-slate-700`}>{formatDateTime(job.created_at)}</td>
      <td className={CELL}>
        <Badge tone={status.tone}>{t(status.label)}</Badge>
      </td>
      <td className={CELL}>
        <InvoiceSummary job={job} />
      </td>
      <td className={`${CELL} text-right`}>
        <div className="flex items-center justify-end gap-1">
          {finished && (
            <Button asChild variant="ghost" size="sm">
              <Link to="/jobs/$jobId/results" params={{ jobId: job.job_id }}>
                {t("jobs.viewResults")}
                <ChevronRight />
              </Link>
            </Button>
          )}
          {finished && <DeleteJobButton jobId={job.job_id} look="icon" />}
        </div>
      </td>
    </tr>
  );
}

function InvoiceSummary({ job }: { job: JobListEntry }) {
  const parts = INVOICE_STATUSES.filter(({ status }) => invoiceCount(job, status) > 0);
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
      <span className="font-medium tabular-nums text-slate-900">{job.invoice_total}</span>
      {parts.map(({ status, label }) => (
        <span key={status} className="text-xs text-slate-500">
          {t("jobs.invoiceCount", { count: invoiceCount(job, status), label: t(label) })}
        </span>
      ))}
    </div>
  );
}

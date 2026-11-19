import { useEffect } from "react";

import { isNotFound } from "@/shared/api/errors";

import { invoiceCount, isJobFinished, jobStatusView } from "./job-status";
import { useRecentJobs } from "./recent-jobs";
import { useJobProgress } from "./use-job-progress";

export interface AlreadyUploadedNotice {
  /** True when no job was created: every file was already in this job (or others). */
  noNewJob: boolean;
  otherJobIds: string[];
}

/**
 * Where the files of an upload already were: none, this job only, or other jobs.
 * The server answers an all-repeated upload with the first earlier job, and lists every
 * earlier job; a new job is never among them.
 *
 * Example:
 *   alreadyUploadedNotice("j1", ["j1", "j0"]) // { noNewJob: true, otherJobIds: ["j0"] }
 */
export function alreadyUploadedNotice(
  jobId: string,
  already: readonly string[],
): AlreadyUploadedNotice | null {
  if (already.length === 0) return null;
  return { noNewJob: already.includes(jobId), otherJobIds: already.filter((id) => id !== jobId) };
}

/**
 * Everything the job screen shows, decided here so the page only presents (§8.2).
 *
 * Example:
 *   const view = useJobView(jobId);
 */
export function useJobView(jobId: string) {
  const query = useJobProgress(jobId);
  const remember = useRecentJobs((state) => state.remember);
  const job = query.data;
  useEffect(() => {
    if (job !== undefined) remember(job.job_id);
  }, [job, remember]);
  if (job === undefined) return { job: undefined, notFound: isNotFound(query.error) } as const;
  return {
    job,
    notFound: false,
    status: jobStatusView(job.status),
    finished: isJobFinished(job.status),
    done: job.invoice_total - invoiceCount(job, "queued"),
    total: job.invoice_total,
  } as const;
}

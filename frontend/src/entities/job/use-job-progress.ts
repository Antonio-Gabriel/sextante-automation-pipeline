import { $api } from "@/shared/api/client";
import { isNotFound } from "@/shared/api/errors";

import { isJobFinished } from "./job-status";

// Polling with a growing interval, stopped when the job is finished (§8.5).
const FIRST_INTERVAL_MS = 500;
const GROWTH = 1.5;
const MAX_INTERVAL_MS = 5000;

/**
 * The wait before the next poll, growing with each answer, failures included.
 *
 * Example:
 *   pollingInterval(2) // 1125
 */
export function pollingInterval(pollsSoFar: number): number {
  return Math.min(FIRST_INTERVAL_MS * GROWTH ** pollsSoFar, MAX_INTERVAL_MS);
}

interface PollState {
  data: { status: string } | undefined;
  error: unknown;
  dataUpdateCount: number;
  errorUpdateCount: number;
}

function nextPoll({ data, error, dataUpdateCount, errorUpdateCount }: PollState): number | false {
  // A job that does not exist will never appear: polling it is waste (§8.5).
  if (isNotFound(error)) return false;
  if (data !== undefined && isJobFinished(data.status)) return false;
  return pollingInterval(dataUpdateCount + errorUpdateCount);
}

/**
 * The job's status and invoice counts, refreshed until it finishes.
 *
 * Example:
 *   const job = useJobProgress(jobId).data;
 */
export function useJobProgress(jobId: string) {
  return $api.useQuery(
    "get",
    "/api/jobs/{job_id}",
    { params: { path: { job_id: jobId } } },
    { refetchInterval: (query) => nextPoll(query.state), retry: false },
  );
}

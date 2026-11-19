import { $api } from "@/shared/api/client";

import { isJobFinished } from "./job-status";

// Polling with a growing interval, stopped when the job is finished (§8.5).
const FIRST_INTERVAL_MS = 500;
const GROWTH = 1.5;
const MAX_INTERVAL_MS = 5000;

export function pollingInterval(pollsSoFar: number): number {
  return Math.min(FIRST_INTERVAL_MS * GROWTH ** pollsSoFar, MAX_INTERVAL_MS);
}

/** The job's status and invoice counts, refreshed until it finishes. */
export function useJobProgress(jobId: string) {
  return $api.useQuery(
    "get",
    "/api/jobs/{job_id}",
    { params: { path: { job_id: jobId } } },
    {
      refetchInterval: (query) => {
        const status = query.state.data?.status;
        return status !== undefined && isJobFinished(status)
          ? false
          : pollingInterval(query.state.dataUpdateCount);
      },
    },
  );
}

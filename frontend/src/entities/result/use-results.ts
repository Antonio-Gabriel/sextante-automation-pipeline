import { $api } from "@/shared/api/client";

import type { ResultFilters } from "./result-filters";

/**
 * One page of the job's coded lines, with the filters of the address.
 *
 * Example:
 *   const page = useResults(jobId, { confidence: "LOW" }).data;
 */
export function useResults(jobId: string, filters: ResultFilters, enabled = true) {
  return $api.useQuery(
    "get",
    "/api/jobs/{job_id}/results",
    {
    params: {
      path: { job_id: jobId },
      query: {
        confidence: filters.confidence ?? null,
        target_sheet: filters.sheet ?? null,
        flagged: filters.flagged ?? null,
        invoice_id: filters.invoice ?? null,
        offset: filters.offset ?? 0,
        ...(filters.limit === undefined ? {} : { limit: filters.limit }),
      },
    },
    },
    { enabled },
  );
}

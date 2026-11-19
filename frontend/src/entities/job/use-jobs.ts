import { $api } from "@/shared/api/client";
import type { components } from "@/shared/api/schema";

export type JobListEntry = components["schemas"]["JobListEntryResponse"];

/**
 * One page of the jobs on the server, newest first; deleted jobs are not listed.
 *
 * Example:
 *   const { data } = useJobs(20, 0);
 */
export function useJobs(limit: number, offset: number) {
  return $api.useQuery("get", "/api/jobs", { params: { query: { limit, offset } } });
}

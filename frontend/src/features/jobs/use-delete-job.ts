import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { useRecentJobs } from "@/entities/job/recent-jobs";
import { $api } from "@/shared/api/client";
import { errorMessage, isKeyReused } from "@/shared/api/errors";
import { queryKeys } from "@/shared/api/query-keys";
import { useIdempotencyKey } from "@/shared/api/use-idempotency-key";
import { t } from "@/shared/i18n/t";

/**
 * Ask, confirm, then delete a finished job, once per key (SEC-19). The job leaves the
 * list and the recent jobs of this browser; the server keeps its records (REQ-PLT-009).
 *
 * Example:
 *   const deletion = useDeleteJob(jobId, () => navigate({ to: "/jobs" }));
 *   deletion.ask(); deletion.confirm();
 */
export function useDeleteJob(jobId: string, onDeleted?: () => Promise<void>) {
  const queryClient = useQueryClient();
  const forget = useRecentJobs((state) => state.forget);
  const keys = useIdempotencyKey();
  const [confirming, setConfirming] = useState(false);
  const mutation = $api.useMutation("delete", "/api/jobs/{job_id}", {
    onSuccess: async () => {
      keys.renew();
      setConfirming(false);
      forget(jobId);
      toast.success(t("jobs.delete.done"));
      await onDeleted?.();
      await queryClient.invalidateQueries({ queryKey: queryKeys.jobList });
    },
    onError: (error) => {
      toast.error(errorMessage(error));
      if (isKeyReused(error)) keys.renew();
      setConfirming(false);
    },
  });
  return {
    confirming,
    isPending: mutation.isPending,
    ask: () => setConfirming(true),
    cancel: () => setConfirming(false),
    confirm: () =>
      mutation.mutate({
        params: { path: { job_id: jobId }, header: { "Idempotency-Key": keys.keyFor(jobId) } },
      }),
  };
}

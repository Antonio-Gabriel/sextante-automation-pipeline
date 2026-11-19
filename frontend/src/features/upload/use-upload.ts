import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";

import { useRecentJobs } from "@/entities/job/recent-jobs";
import { $api } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/errors";
import { queryKeys } from "@/shared/api/query-keys";

/**
 * Sends the files; on success opens the job, saying where already uploaded files are and
 * which deleted jobs the upload brought back (REQ-PLT-009).
 */
export function useUpload() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const remember = useRecentJobs((state) => state.remember);
  const mutation = $api.useMutation("post", "/api/invoices", {
    onSuccess: async (receipt) => {
      remember(receipt.job_id);
      const { existing_job_ids: already, restored_job_ids: restored } = receipt;
      await queryClient.invalidateQueries({ queryKey: queryKeys.jobList });
      await navigate({
        to: "/jobs/$jobId",
        params: { jobId: receipt.job_id },
        search: {
          ...(already.length > 0 ? { already } : {}),
          ...(restored.length > 0 ? { restored } : {}),
        },
      });
    },
    onError: (error) => {
      toast.error(errorMessage(error));
    },
  });
  const upload = (files: readonly File[]) =>
    mutation.mutate({
      // The typed body the contract asks for; the serializer below sends it as multipart.
      body: { files: [...files] },
      // Each part carries its file name explicitly: the server records and checks it.
      bodySerializer: () => {
        const form = new FormData();
        for (const file of files) form.append("files", file, file.name);
        return form;
      },
    });
  return { upload, isPending: mutation.isPending };
}

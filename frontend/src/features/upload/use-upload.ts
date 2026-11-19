import { useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";

import { useRecentJobs } from "@/entities/job/recent-jobs";
import { $api } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/errors";

/** Sends the files; on success opens the job, saying where already uploaded files are. */
export function useUpload() {
  const navigate = useNavigate();
  const remember = useRecentJobs((state) => state.remember);
  const mutation = $api.useMutation("post", "/api/invoices", {
    onSuccess: async (receipt) => {
      remember(receipt.job_id);
      const already = receipt.existing_job_ids;
      await navigate({
        to: "/jobs/$jobId",
        params: { jobId: receipt.job_id },
        search: already.length > 0 ? { already } : {},
      });
    },
    onError: (error) => {
      toast.error(errorMessage(error));
    },
  });
  const upload = (files: readonly File[]) =>
    mutation.mutate({
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

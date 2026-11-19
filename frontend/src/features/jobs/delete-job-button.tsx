import { Trash2 } from "lucide-react";

import { shortJobId } from "@/entities/job/job-status";
import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";
import { ConfirmDialog } from "@/shared/ui-kit/confirm-dialog";
import { useConfirmationFocus } from "@/shared/ui-kit/use-confirmation-focus";

import { useDeleteJob } from "./use-delete-job";

interface DeleteJobButtonProps {
  jobId: string;
  /** "icon" in a table row, "full" in a page header. */
  look: "icon" | "full";
  onDeleted?: () => Promise<void>;
}

/**
 * Delete a finished job, after a modal confirmation that says what stays and how it returns.
 *
 * Example:
 *   <DeleteJobButton jobId={job.job_id} look="icon" />
 */
export function DeleteJobButton({ jobId, look, onDeleted }: DeleteJobButtonProps) {
  const deletion = useDeleteJob(jobId, onDeleted);
  const focus = useConfirmationFocus(deletion.confirming, deletion.cancel);
  const label = t("jobs.delete.action", { id: shortJobId(jobId) });
  return (
    <>
      {look === "icon" ? (
        <Button ref={focus.trigger} variant="ghost" size="icon" aria-label={label} title={label} onClick={deletion.ask} className="text-slate-400 hover:bg-red-50 hover:text-red-600">
          <Trash2 />
        </Button>
      ) : (
        <Button ref={focus.trigger} variant="outline" onClick={deletion.ask} className="text-red-700 hover:bg-red-50">
          <Trash2 />
          {t("jobs.delete.short")}
        </Button>
      )}
      {deletion.confirming && (
        <ConfirmDialog
          focus={focus}
          icon={<Trash2 />}
          title={t("jobs.delete.confirmTitle", { id: shortJobId(jobId) })}
          body={t("jobs.delete.confirmBody")}
          confirmLabel={t("jobs.delete.confirm")}
          pendingLabel={t("jobs.delete.sending")}
          cancelLabel={t("jobs.delete.cancel")}
          pending={deletion.isPending}
          onConfirm={deletion.confirm}
          onCancel={deletion.cancel}
        />
      )}
    </>
  );
}

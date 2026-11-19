import { Upload } from "lucide-react";

import { LatestJobs } from "@/features/jobs/latest-jobs";
import { FileDropzone } from "@/features/upload/file-dropzone";
import { SelectedFiles } from "@/features/upload/selected-files";
import { UploadHints } from "@/features/upload/upload-hints";
import { useFileSelection } from "@/features/upload/use-file-selection";
import { useUpload } from "@/features/upload/use-upload";
import { Page } from "@/shared/layout/page";
import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";
import { Card, CardContent } from "@/shared/ui-kit/card";

/** Choose or drop PDF invoices and send them; the job screen follows the work. */
export function UploadPage() {
  const selection = useFileSelection();
  const { upload, isPending } = useUpload();
  const count = selection.files.length;
  const hasFiles = count > 0;

  return (
    <Page title={t("upload.title")} description={t("upload.description")}>
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 xl:pt-4">
        <Card>
          <CardContent className="flex flex-col gap-5 p-6">
            <FileDropzone onFiles={selection.add} disabled={isPending} compact={hasFiles} />
            {hasFiles && (
              <>
                <SelectedFiles files={selection.files} onRemove={selection.remove} onClear={selection.clear} disabled={isPending} />
                <Button className="h-10 w-full" disabled={isPending} onClick={() => upload(selection.files)}>
                  <Upload />
                  {isPending ? t("upload.submitting") : count === 1 ? t("upload.submitOne") : t("upload.submit", { count })}
                </Button>
              </>
            )}
          </CardContent>
        </Card>
        <UploadHints />
        <LatestJobs />
      </div>
    </Page>
  );
}

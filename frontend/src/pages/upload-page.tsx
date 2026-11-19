import { Upload } from "lucide-react";

import { FileDropzone } from "@/features/upload/file-dropzone";
import { SelectedFiles } from "@/features/upload/selected-files";
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
  const hasFiles = selection.files.length > 0;

  return (
    <Page title={t("upload.title")} description={t("upload.description")}>
      <Card className="max-w-2xl">
        <CardContent className="flex flex-col gap-4 pt-5">
          <FileDropzone onFiles={selection.add} disabled={isPending} />
          {hasFiles && (
            <>
              <SelectedFiles files={selection.files} onRemove={selection.remove} disabled={isPending} />
              <div className="flex justify-end gap-2">
                <Button variant="ghost" disabled={isPending} onClick={selection.clear}>
                  {t("upload.clear")}
                </Button>
                <Button disabled={isPending} onClick={() => upload(selection.files)}>
                  <Upload />
                  {isPending ? t("upload.submitting") : t("upload.submit", { count: selection.files.length })}
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </Page>
  );
}

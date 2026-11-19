import { Download } from "lucide-react";

import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";

import { EXPORT_FORMATS, useExport } from "./use-export";

/**
 * One button per export format; both wait while a file is being made.
 *
 * Example:
 *   <ExportButtons jobId={jobId} />
 */
export function ExportButtons({ jobId }: { jobId: string }) {
  const exporter = useExport(jobId);
  return (
    <>
      {EXPORT_FORMATS.map((format) => (
        <Button key={format} variant="outline" disabled={exporter.isPending} onClick={() => exporter.download(format)}>
          <Download />
          {exporter.pendingFormat === format ? t("export.exporting") : t(`export.${format}`)}
        </Button>
      ))}
    </>
  );
}

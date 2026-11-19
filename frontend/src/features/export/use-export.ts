import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

import type { components } from "@/shared/api/schema";
import { fetchClient } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/errors";
import { t } from "@/shared/i18n/t";

type ExportFormat = components["schemas"]["ExportFormat"];

export const EXPORT_FORMATS = ["csv", "xlsx"] as const satisfies readonly ExportFormat[];

// The server names the file (SEC-16); the page only reads the name it sent.
const FILE_NAME = /filename="([^"]+)"/;
const FALLBACK_NAME = "sextante-export";

/**
 * The file name the server gave in Content-Disposition.
 *
 * Example:
 *   fileNameOf('attachment; filename="sextante-j1.csv"') // "sextante-j1.csv"
 */
export function fileNameOf(disposition: string | null): string {
  return disposition?.match(FILE_NAME)?.[1] ?? FALLBACK_NAME;
}

function save(blob: Blob, fileName: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = fileName;
  link.click();
  URL.revokeObjectURL(url);
}

async function download(jobId: string, format: ExportFormat) {
  // Through the one client, with the session cookie; an error comes back as its body.
  const { data, error, response } = await fetchClient.GET("/api/exports/{job_id}", {
    params: { path: { job_id: jobId }, query: { format } },
    parseAs: "blob",
  });
  if (data === undefined) throw error;
  save(data, fileNameOf(response.headers.get("Content-Disposition")));
}

/**
 * Download the job's export as CSV or XLSX, with the person's session.
 *
 * Example:
 *   const exporter = useExport(jobId);
 *   exporter.mutate("xlsx");
 */
export function useExport(jobId: string) {
  return useMutation({
    mutationFn: (format: ExportFormat) => download(jobId, format),
    onSuccess: () => toast.success(t("export.done")),
    onError: (error) => {
      toast.error(errorMessage(error));
    },
  });
}

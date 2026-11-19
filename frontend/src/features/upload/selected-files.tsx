import { X } from "lucide-react";

import { t, tCount } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";

import { formatBytes } from "./format-bytes";
import { fileKey } from "./use-file-selection";

interface SelectedFilesProps {
  files: readonly File[];
  onRemove: (file: File) => void;
  onClear: () => void;
  disabled: boolean;
}

/** The files about to be sent: how many and how large, each with a way to take it out. */
export function SelectedFiles({ files, onRemove, onClear, disabled }: SelectedFilesProps) {
  const size = formatBytes(files.reduce((total, file) => total + file.size, 0));
  return (
    <section className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-medium text-slate-700">
          {tCount(files.length, "upload.summaryOne", "upload.summary", { size })}
        </p>
        <Button variant="ghost" size="sm" disabled={disabled} onClick={onClear}>
          {t("upload.clear")}
        </Button>
      </div>
      <ul aria-label={t("upload.selected")} className="flex max-h-80 flex-col divide-y divide-slate-100 overflow-y-auto rounded-lg border border-slate-200">
        {files.map((file) => (
          <li key={fileKey(file)} className="flex items-center gap-3 bg-white px-3 py-2.5">
            <span className="flex h-9 w-8 shrink-0 items-center justify-center rounded-md bg-red-50 text-[10px] font-semibold text-red-700 ring-1 ring-red-100" aria-hidden>
              {t("upload.pdf")}
            </span>
            <span className="min-w-0 flex-1 truncate text-sm text-slate-900">{file.name}</span>
            <span className="text-xs tabular-nums text-slate-500">{formatBytes(file.size)}</span>
            <Button
              variant="ghost"
              size="icon"
              disabled={disabled}
              aria-label={t("upload.remove", { name: file.name })}
              onClick={() => onRemove(file)}
            >
              <X />
            </Button>
          </li>
        ))}
      </ul>
    </section>
  );
}

import { FileText, X } from "lucide-react";

import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";

import { formatBytes } from "./format-bytes";

interface SelectedFilesProps {
  files: readonly File[];
  onRemove: (file: File) => void;
  disabled: boolean;
}

export function SelectedFiles({ files, onRemove, disabled }: SelectedFilesProps) {
  return (
    <ul aria-label={t("upload.selected")} className="flex flex-col gap-2">
      {files.map((file) => (
        <li
          key={`${file.name}:${file.size}`}
          className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2"
        >
          <FileText className="size-5 shrink-0 text-red-600" aria-hidden />
          <span className="min-w-0 flex-1 truncate text-sm text-slate-900">{file.name}</span>
          <span className="text-xs tabular-nums text-slate-500">{formatBytes(file.size)}</span>
          <Button
            variant="ghost"
            size="icon"
            disabled={disabled}
            aria-label={`${t("upload.remove")} ${file.name}`}
            onClick={() => onRemove(file)}
          >
            <X />
          </Button>
        </li>
      ))}
    </ul>
  );
}

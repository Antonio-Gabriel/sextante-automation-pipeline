import { CloudUpload } from "lucide-react";
import { useRef, useState, type DragEvent } from "react";

import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";
import { cn } from "@/shared/ui-kit/cn";

interface FileDropzoneProps {
  onFiles: (files: FileList) => void;
  disabled: boolean;
}

/**
 * Drop files here, or pick them; the server is the one that checks them.
 *
 * Example:
 *   <FileDropzone onFiles={selection.add} disabled={isPending} />
 */
export function FileDropzone({ onFiles, disabled }: FileDropzoneProps) {
  const input = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const onDrop = (event: DragEvent) => {
    event.preventDefault();
    setDragging(false);
    if (!disabled) onFiles(event.dataTransfer.files);
  };

  return (
    <div
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(!disabled);
      }}
      onDragLeave={(event) => {
        // Moving over a child also fires dragleave: only leaving the zone itself counts.
        const into = event.relatedTarget;
        if (!(into instanceof Node && event.currentTarget.contains(into))) setDragging(false);
      }}
      onDrop={onDrop}
      className={cn(
        "flex flex-col items-center gap-3 rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center transition-colors",
        dragging && "border-brand-400 bg-brand-50",
      )}
    >
      <span className="flex size-12 items-center justify-center rounded-full bg-white text-brand-700 shadow-xs ring-1 ring-slate-200">
        <CloudUpload className="size-6" />
      </span>
      <p className="font-medium text-slate-900">{t("upload.dropTitle")}</p>
      <p className="text-sm text-slate-500">{t("upload.dropHint")}</p>
      <Button variant="outline" disabled={disabled} onClick={() => input.current?.click()}>
        {t("upload.choose")}
      </Button>
      <input
        ref={input}
        type="file"
        multiple
        accept="application/pdf,.pdf"
        aria-label={t("upload.inputLabel")}
        className="sr-only"
        onChange={(event) => {
          if (event.target.files !== null) onFiles(event.target.files);
          event.target.value = "";
        }}
      />
    </div>
  );
}

import { CopyCheck, FileText, Timer } from "lucide-react";
import type { ReactNode } from "react";

import { t, type MessageKey } from "@/shared/i18n/t";

const HINTS: readonly { icon: ReactNode; title: MessageKey; text: MessageKey }[] = [
  { icon: <FileText />, title: "upload.hints.nativeTitle", text: "upload.hints.native" },
  { icon: <CopyCheck />, title: "upload.hints.repeatTitle", text: "upload.hints.repeat" },
  { icon: <Timer />, title: "upload.hints.backgroundTitle", text: "upload.hints.background" },
];

/** What the server does with an upload, said before it is sent. */
export function UploadHints() {
  return (
    <ul aria-label={t("upload.hints.label")} className="grid gap-3 sm:grid-cols-3">
      {HINTS.map((hint) => (
        <li key={hint.title} className="flex gap-3 rounded-xl border border-slate-200 bg-white p-4">
          <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-700 [&_svg]:size-4" aria-hidden>
            {hint.icon}
          </span>
          <div className="flex flex-col gap-0.5">
            <p className="text-sm font-medium text-slate-900">{t(hint.title)}</p>
            <p className="text-xs leading-relaxed text-slate-500">{t(hint.text)}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}

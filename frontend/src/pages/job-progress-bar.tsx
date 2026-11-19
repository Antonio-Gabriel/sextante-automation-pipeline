import { t } from "@/shared/i18n/t";

interface JobProgressBarProps {
  counts: Record<string, number>;
  total: number;
}

/** How many invoices of the job are no longer waiting. */
export function JobProgressBar({ counts, total }: JobProgressBarProps) {
  const done = total - (counts["queued"] ?? 0);
  const percent = total === 0 ? 0 : Math.round((done / total) * 100);
  return (
    <div className="flex flex-1 items-center gap-3">
      <div
        role="progressbar"
        aria-label={t("job.progress")}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={done}
        className="h-2 max-w-md flex-1 overflow-hidden rounded-full bg-slate-200"
      >
        <div className="h-full rounded-full bg-brand-700 transition-[width]" style={{ width: `${percent}%` }} />
      </div>
      <span className="text-sm tabular-nums text-slate-600">
        {done}/{total} {t("job.processed")}
      </span>
    </div>
  );
}

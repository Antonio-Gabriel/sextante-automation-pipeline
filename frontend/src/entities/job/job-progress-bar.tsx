import { t } from "@/shared/i18n/t";

interface JobProgressBarProps {
  done: number;
  total: number;
}

/**
 * How many invoices of the job are no longer waiting.
 *
 * Example:
 *   <JobProgressBar done={3} total={5} />
 */
export function JobProgressBar({ done, total }: JobProgressBarProps) {
  const percent = total === 0 ? 0 : Math.round((done / total) * 100);
  return (
    <div className="flex flex-1 items-center gap-3">
      <div
        role="progressbar"
        aria-label={t("job.progress")}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
        aria-valuetext={t("job.processed", { done, total })}
        className="h-2 max-w-md flex-1 overflow-hidden rounded-full bg-slate-200"
      >
        <div className="h-full rounded-full bg-brand-700 transition-[width]" style={{ width: `${percent}%` }} />
      </div>
      <span className="text-sm tabular-nums text-slate-600">{t("job.processed", { done, total })}</span>
    </div>
  );
}

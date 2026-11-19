import type { MessageKey } from "@/shared/i18n/t";
import type { BadgeTone } from "@/shared/ui-kit/badge";

// The closed sets of the server (JobStatus, InvoiceStatus), each with its text and tone.
const JOB_STATUSES = {
  queued: { label: "job.status.queued", tone: "neutral" },
  running: { label: "job.status.running", tone: "brand" },
  waiting_model: { label: "job.status.waiting_model", tone: "warning" },
  completed: { label: "job.status.completed", tone: "success" },
  failed: { label: "job.status.failed", tone: "danger" },
} as const satisfies Record<string, { label: MessageKey; tone: BadgeTone }>;

type JobStatus = keyof typeof JOB_STATUSES;

const FINISHED: ReadonlySet<string> = new Set<JobStatus>(["completed", "failed"]);

export const INVOICE_STATUSES = [
  { status: "queued", label: "job.invoices.queued" },
  { status: "encoded", label: "job.invoices.encoded" },
  { status: "not_coded", label: "job.invoices.not_coded" },
  { status: "rejected", label: "job.invoices.rejected" },
  { status: "failed", label: "job.invoices.failed" },
] as const satisfies readonly { status: string; label: MessageKey }[];

function isJobStatus(status: string): status is JobStatus {
  return Object.hasOwn(JOB_STATUSES, status);
}

/** Text and tone of a job status; an unknown one is shown as such, never hidden. */
export function jobStatusView(status: string): { label: MessageKey; tone: BadgeTone } {
  return isJobStatus(status) ? JOB_STATUSES[status] : { label: "job.status.unknown", tone: "neutral" };
}

/** Whether the job will change no more: polling stops there (§8.5). */
export function isJobFinished(status: string): boolean {
  return FINISHED.has(status);
}

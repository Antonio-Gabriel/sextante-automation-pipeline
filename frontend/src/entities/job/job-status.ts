import type { components } from "@/shared/api/schema";
import type { MessageKey } from "@/shared/i18n/t";
import type { BadgeTone } from "@/shared/ui-kit/badge";

type JobProgress = components["schemas"]["JobProgressResponse"];

// The closed sets of the server (JobStatus, InvoiceStatus), each with its text and tone.
const JOB_STATUSES = {
  queued: { label: "job.status.queued", tone: "neutral" },
  running: { label: "job.status.running", tone: "brand" },
  waiting_model: { label: "job.status.waiting_model", tone: "warning" },
  completed: { label: "job.status.completed", tone: "success" },
  failed: { label: "job.status.failed", tone: "danger" },
} as const satisfies Record<string, { label: MessageKey; tone: BadgeTone }>;

export type JobStatus = keyof typeof JOB_STATUSES;

const FINISHED: ReadonlySet<JobStatus> = new Set<JobStatus>(["completed", "failed"]);
const UNKNOWN = { label: "job.status.unknown", tone: "neutral" } as const;

export const INVOICE_STATUSES = [
  { status: "queued", label: "job.invoices.queued" },
  { status: "encoded", label: "job.invoices.encoded" },
  { status: "not_coded", label: "job.invoices.not_coded" },
  { status: "rejected", label: "job.invoices.rejected" },
  { status: "failed", label: "job.invoices.failed" },
] as const satisfies readonly { status: string; label: MessageKey }[];

export type InvoiceStatus = (typeof INVOICE_STATUSES)[number]["status"];

function isJobStatus(status: string): status is JobStatus {
  return Object.hasOwn(JOB_STATUSES, status);
}

/**
 * Text and tone of a job status; an unknown one is shown as such, never hidden.
 *
 * Example:
 *   jobStatusView("completed") // { label: "job.status.completed", tone: "success" }
 */
export function jobStatusView(status: string): { label: MessageKey; tone: BadgeTone } {
  return isJobStatus(status) ? JOB_STATUSES[status] : UNKNOWN;
}

/**
 * Whether the job will change no more. Queued and waiting jobs still change, so the
 * page keeps polling them; only completed and failed stop it (§8.5).
 *
 * Example:
 *   isJobFinished("waiting_model") // false
 */
export function isJobFinished(status: string): boolean {
  return isJobStatus(status) && FINISHED.has(status);
}

/**
 * How many invoices of a job are in one state.
 *
 * Example:
 *   invoiceCount(job, "encoded") // 3
 */
export function invoiceCount(job: JobProgress, status: InvoiceStatus): number {
  return job.invoice_counts[status] ?? 0;
}

/**
 * The first eight characters of a job id, enough to tell jobs apart on screen.
 *
 * Example:
 *   shortJobId("3f2a9c0d-1e4b-...") // "3f2a9c0d"
 */
export function shortJobId(jobId: string): string {
  return jobId.slice(0, 8);
}

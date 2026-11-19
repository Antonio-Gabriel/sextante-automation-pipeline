import { INVOICE_STATUSES } from "@/entities/job/job-status";
import type { LabelledTone } from "@/entities/result/result-labels";

// The entity verdicts of the server (REQ-ENT-004), as the screen shows them.
const VERDICTS = {
  MATCH: { label: "invoice.verdict.MATCH", tone: "success" },
  NO_MATCH: { label: "invoice.verdict.NO_MATCH", tone: "neutral" },
  AMBIGUOUS: { label: "invoice.verdict.AMBIGUOUS", tone: "warning" },
} as const satisfies Record<string, LabelledTone>;

const INVOICE_TONES = {
  queued: "neutral",
  encoded: "success",
  not_coded: "warning",
  rejected: "danger",
  failed: "danger",
} as const;

function isVerdict(value: string | null): value is keyof typeof VERDICTS {
  return value !== null && Object.hasOwn(VERDICTS, value);
}

/**
 * Text and tone of an entity verdict; none before the check.
 *
 * Example:
 *   verdictView("AMBIGUOUS") // { label: "invoice.verdict.AMBIGUOUS", tone: "warning" }
 */
export function verdictView(verdict: string | null): LabelledTone | null {
  return isVerdict(verdict) ? VERDICTS[verdict] : null;
}

/**
 * Text and tone of an invoice status, from the same labels as the job screen.
 *
 * Example:
 *   invoiceStatusView("not_coded") // { label: "job.invoices.not_coded", tone: "warning" }
 */
export function invoiceStatusView(status: string): LabelledTone {
  const known = INVOICE_STATUSES.find((entry) => entry.status === status);
  if (known === undefined) return { label: "job.status.unknown", tone: "neutral" };
  return { label: known.label, tone: INVOICE_TONES[known.status] };
}

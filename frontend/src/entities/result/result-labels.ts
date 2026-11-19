import type { components } from "@/shared/api/schema";
import type { MessageKey } from "@/shared/i18n/t";
import type { BadgeTone } from "@/shared/ui-kit/badge";

type Confidence = components["schemas"]["Confidence"];

/** A server code as the screen shows it: Portuguese text and the tone of its badge. */
export interface LabelledTone {
  label: MessageKey;
  tone: BadgeTone;
}

// Server codes shown as Portuguese text: the code never reaches the screen (§8.6).
const CONFIDENCE: Record<Confidence, LabelledTone> = {
  HIGH: { label: "values.confidence.HIGH", tone: "success" },
  MEDIUM: { label: "values.confidence.MEDIUM", tone: "warning" },
  LOW: { label: "values.confidence.LOW", tone: "danger" },
};

const REVIEW = {
  pending: { label: "values.review.pending", tone: "warning" },
  accepted: { label: "values.review.accepted", tone: "success" },
  corrected: { label: "values.review.corrected", tone: "brand" },
} as const satisfies Record<string, LabelledTone>;

const NO_REVIEW: LabelledTone = { label: "values.review.none", tone: "neutral" };

function isConfidence(value: string | null): value is Confidence {
  return value !== null && Object.hasOwn(CONFIDENCE, value);
}

function isReviewStatus(value: string | null): value is keyof typeof REVIEW {
  return value !== null && Object.hasOwn(REVIEW, value);
}

/**
 * Text and tone of a confidence, or null for a line without one.
 *
 * Example:
 *   confidenceView("LOW") // { label: "values.confidence.LOW", tone: "danger" }
 */
export function confidenceView(confidence: string | null): LabelledTone | null {
  return isConfidence(confidence) ? CONFIDENCE[confidence] : null;
}

/**
 * Text and tone of a review status; a line not yet coded has none.
 *
 * Example:
 *   reviewView("corrected") // { label: "values.review.corrected", tone: "brand" }
 */
export function reviewView(status: string | null): LabelledTone {
  return isReviewStatus(status) ? REVIEW[status] : NO_REVIEW;
}

/**
 * The text of the export's YES/NO values.
 *
 * Example:
 *   t(yesNo("YES")) // "Sim"
 */
export function yesNo(value: string): MessageKey {
  return value === "YES" ? "values.yes" : "values.no";
}

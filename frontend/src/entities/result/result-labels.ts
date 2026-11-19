import type { MessageKey } from "@/shared/i18n/t";
import type { BadgeTone } from "@/shared/ui-kit/badge";

// Server codes shown as Portuguese text: the code never reaches the screen (§8.6).
const CONFIDENCE = {
  HIGH: { label: "values.confidence.HIGH", tone: "success" },
  MEDIUM: { label: "values.confidence.MEDIUM", tone: "warning" },
  LOW: { label: "values.confidence.LOW", tone: "danger" },
} as const satisfies Record<string, { label: MessageKey; tone: BadgeTone }>;

const REVIEW = {
  pending: { label: "values.review.pending", tone: "warning" },
  accepted: { label: "values.review.accepted", tone: "success" },
  corrected: { label: "values.review.corrected", tone: "brand" },
} as const satisfies Record<string, { label: MessageKey; tone: BadgeTone }>;

const NONE = { label: "values.review.none", tone: "neutral" } as const;

export function confidenceView(confidence: string | null) {
  return confidence !== null && Object.hasOwn(CONFIDENCE, confidence)
    ? CONFIDENCE[confidence as keyof typeof CONFIDENCE] // narrowed by Object.hasOwn above
    : null;
}

export function reviewView(status: string | null): { label: MessageKey; tone: BadgeTone } {
  return status !== null && Object.hasOwn(REVIEW, status)
    ? REVIEW[status as keyof typeof REVIEW] // narrowed by Object.hasOwn above
    : NONE;
}

export function yesNo(value: string): MessageKey {
  return value === "YES" ? "values.yes" : "values.no";
}

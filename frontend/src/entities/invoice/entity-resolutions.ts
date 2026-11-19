import type { components } from "@/shared/api/schema";
import type { MessageKey } from "@/shared/i18n/t";

type Resolution = components["schemas"]["EntityResolutionRequest"]["resolution"];

// The two resolutions a reviewer may record (REQ-REV-006), each with its text; one list
// for the choices, the form schema and the recorded resolution.
export const RESOLUTIONS = ["MATCH", "NO_MATCH"] as const satisfies readonly Resolution[];

const LABELS: Record<Resolution, MessageKey> = {
  MATCH: "invoice.resolution.MATCH",
  NO_MATCH: "invoice.resolution.NO_MATCH",
};

/**
 * The text of a resolution, or null for a value this screen does not know.
 *
 * Example:
 *   resolutionLabel("NO_MATCH") // "invoice.resolution.NO_MATCH"
 */
export function resolutionLabel(verdict: string): MessageKey | null {
  const known = RESOLUTIONS.find((resolution) => resolution === verdict);
  return known === undefined ? null : LABELS[known];
}

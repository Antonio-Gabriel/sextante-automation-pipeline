import { z } from "zod";

import type { components } from "@/shared/api/schema";

type Confidence = components["schemas"]["Confidence"];
type TargetSheet = components["schemas"]["TargetSheet"];

export const CONFIDENCES = ["HIGH", "MEDIUM", "LOW"] as const satisfies readonly Confidence[];
export const TARGET_SHEETS = ["OUTLAYS", "OUTLAYSP"] as const satisfies readonly TargetSheet[];
const IDENTIFIER = /^[A-Za-z0-9_-]{1,64}$/;

// The view lives in the address, so a reviewer can send it to a colleague (§8.3). Each
// field is checked on its own: an invalid one is dropped, the others are kept.
export const resultFiltersSchema = z.object({
  confidence: z.enum(CONFIDENCES).optional().catch(undefined),
  sheet: z.enum(TARGET_SHEETS).optional().catch(undefined),
  flagged: z.boolean().optional().catch(undefined),
  invoice: z.string().regex(IDENTIFIER).optional().catch(undefined),
  offset: z.number().int().min(0).optional().catch(undefined),
  limit: z.number().int().min(1).optional().catch(undefined),
});

export type ResultFilters = z.infer<typeof resultFiltersSchema>;

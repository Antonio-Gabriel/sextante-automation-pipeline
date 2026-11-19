import { $api } from "@/shared/api/client";
import type { MessageKey } from "@/shared/i18n/t";

export type HealthState = "loading" | "up" | "down";

export interface ServerHealth {
  state: HealthState;
  label: MessageKey;
  catalogDigest: string | undefined;
}

const LABELS: Record<HealthState, MessageKey> = {
  loading: "health.loading",
  up: "health.up",
  down: "health.down",
};

/** Whether the server is up, and which catalog it serves. */
export function useHealth(): ServerHealth {
  const health = $api.useQuery("get", "/api/health");
  const state: HealthState = health.isPending ? "loading" : health.data ? "up" : "down";
  return { state, label: LABELS[state], catalogDigest: health.data?.catalog_digest };
}

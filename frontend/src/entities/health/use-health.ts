import { $api } from "@/shared/api/client";
import type { MessageKey } from "@/shared/i18n/t";

// One record per state: its text and the colour of its dot.
const HEALTH_STATES = {
  loading: { label: "health.loading", dot: "bg-slate-300" },
  up: { label: "health.up", dot: "bg-emerald-500" },
  down: { label: "health.down", dot: "bg-red-500" },
} as const satisfies Record<string, { label: MessageKey; dot: string }>;

type HealthState = keyof typeof HEALTH_STATES;

/**
 * Whether the server is up, which release it runs and which catalog it serves.
 *
 * Example:
 *   const { label, dot, catalogDigest, version } = useHealth();
 */
export function useHealth() {
  const health = $api.useQuery("get", "/api/health");
  const state: HealthState = health.isPending ? "loading" : health.data ? "up" : "down";
  return { ...HEALTH_STATES[state], catalogDigest: health.data?.catalog_digest, version: health.data?.version };
}

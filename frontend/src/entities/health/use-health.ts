import { $api } from "@/shared/api/client";
import type { MessageKey } from "@/shared/i18n/t";

export interface ServerHealth {
  status: MessageKey;
  catalogDigest: string | undefined;
}

/** Whether the server is up, and which catalog it serves. */
export function useHealth(): ServerHealth {
  const health = $api.useQuery("get", "/api/health");
  const status: MessageKey = health.isPending
    ? "home.loading"
    : health.data
      ? "home.serverUp"
      : "home.serverDown";
  return { status, catalogDigest: health.data?.catalog_digest };
}

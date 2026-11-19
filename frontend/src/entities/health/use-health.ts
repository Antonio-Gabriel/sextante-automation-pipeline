import { $api } from "@/shared/api/client";

/** Whether the server is up, and which catalog it serves. */
export function useHealth() {
  return $api.useQuery("get", "/api/health");
}

import { QueryClient } from "@tanstack/react-query";

import { isNotFound, isUnauthenticated } from "@/shared/api/errors";

const MAX_RETRIES = 2;

/** Server state lives here (§8.3). A refused credential or a missing resource is never retried. */
export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: (failures, error) =>
          !isUnauthenticated(error) && !isNotFound(error) && failures < MAX_RETRIES,
      },
    },
  });
}

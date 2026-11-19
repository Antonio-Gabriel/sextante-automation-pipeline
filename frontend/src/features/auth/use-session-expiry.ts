import {
  useQueryClient,
  type MutationCacheNotifyEvent,
  type QueryCacheNotifyEvent,
} from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";

import { isUnauthenticated } from "@/shared/api/errors";

type CacheEvent = QueryCacheNotifyEvent | MutationCacheNotifyEvent;

/** Returns to login when the server refuses a request for want of a session. */
export function useSessionExpiry() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  useEffect(() => {
    const onEvent = (event: CacheEvent) => {
      if (event.type === "updated" && event.action.type === "error" && isUnauthenticated(event.action.error)) {
        queryClient.clear();
        void navigate({ to: "/login" });
      }
    };
    const queries = queryClient.getQueryCache().subscribe(onEvent);
    const mutations = queryClient.getMutationCache().subscribe(onEvent);
    return () => {
      queries();
      mutations();
    };
  }, [queryClient, navigate]);
}

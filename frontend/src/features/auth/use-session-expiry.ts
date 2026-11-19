import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";

import { isUnauthenticated } from "@/shared/api/errors";

/** Returns to login when the server refuses a request for want of a session. */
export function useSessionExpiry() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  useEffect(() => {
    const onRefused = (error: unknown) => {
      if (isUnauthenticated(error)) {
        queryClient.clear();
        void navigate({ to: "/login" });
      }
    };
    const queries = queryClient.getQueryCache().subscribe((event) => {
      if (event.type === "updated" && event.action.type === "error") onRefused(event.action.error);
    });
    const mutations = queryClient.getMutationCache().subscribe((event) => {
      if (event.type === "updated" && event.action.type === "error") onRefused(event.action.error);
    });
    return () => {
      queries();
      mutations();
    };
  }, [queryClient, navigate]);
}

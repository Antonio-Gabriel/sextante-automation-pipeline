import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";

import { $api } from "@/shared/api/client";

/** Ends the session in the server, forgets every cached answer, and returns to login. */
export function useLogout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  return $api.useMutation("post", "/api/session/end", {
    onSettled: async () => {
      queryClient.clear();
      await navigate({ to: "/login" });
    },
  });
}

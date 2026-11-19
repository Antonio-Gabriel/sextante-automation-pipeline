import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";

import { $api } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/errors";

/**
 * Ends the session in the server, then forgets every cached answer and returns to login.
 * When the server does not confirm, the person stays, told why: the session may be open.
 */
export function useLogout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  return $api.useMutation("post", "/api/session/end", {
    onSuccess: async () => {
      queryClient.clear();
      await navigate({ to: "/login" });
    },
    onError: (error) => {
      toast.error(errorMessage(error));
    },
  });
}

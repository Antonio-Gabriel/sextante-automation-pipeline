import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";

import { sessionQuery } from "@/entities/session/session-query";
import { $api } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/errors";

/** Sends the access token; the server answers with the session cookie, or refuses. */
export function useLogin() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  return $api.useMutation("post", "/api/session", {
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: sessionQuery.queryKey });
      await navigate({ to: "/" });
    },
    onError: (error) => {
      toast.error(errorMessage(error));
    },
  });
}

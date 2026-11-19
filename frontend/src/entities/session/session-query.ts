import { $api } from "@/shared/api/client";

/** Answers when the browser holds an open session; the server refuses with 401 otherwise. */
export const sessionQuery = $api.queryOptions("get", "/api/session");

import { t } from "@/shared/i18n/t";

import type { components } from "./schema";

type ErrorResponse = components["schemas"]["ErrorResponse"];

const CREDENTIAL_INVALID = "errors.auth.credential_invalid";
const NOT_FOUND = /^errors\.[a-z_]+\.not_found$/;

function isErrorResponse(error: unknown): error is ErrorResponse {
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    "message" in error &&
    typeof error.code === "string" &&
    typeof error.message === "string"
  );
}

/** The Portuguese message the server sent, or the catalog's when there is none. */
export function errorMessage(error: unknown): string {
  return isErrorResponse(error) ? error.message : t("errors.unexpected");
}

/** Whether the server refused the request for want of a session or key. */
export function isUnauthenticated(error: unknown): boolean {
  return isErrorResponse(error) && error.code === CREDENTIAL_INVALID;
}

/** Whether the server said the resource does not exist (errors.<thing>.not_found). */
export function isNotFound(error: unknown): boolean {
  return isErrorResponse(error) && NOT_FOUND.test(error.code);
}

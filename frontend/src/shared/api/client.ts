// The one HTTP client of the application (04-padroes-de-codigo.md §8.5). Same origin:
// the browser sends the HttpOnly session cookie by itself, and never holds the API key.
import createFetchClient from "openapi-fetch";
import createClient from "openapi-react-query";

import { currentLanguage } from "@/shared/i18n/language";

import type { paths } from "./schema";

export const fetchClient = createFetchClient<paths>({
  baseUrl: globalThis.location?.origin ?? "",
  credentials: "same-origin",
  // Looked up on each call, so a test's network double sees every request.
  fetch: (request) => globalThis.fetch(request),
});

// Every request names the interface language: the server answers its texts in it.
fetchClient.use({
  onRequest({ request }) {
    request.headers.set("Accept-Language", currentLanguage());
    return request;
  },
});

export const $api = createClient(fetchClient);

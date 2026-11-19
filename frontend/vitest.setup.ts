import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { toast } from "sonner";
import { afterAll, afterEach, beforeAll, beforeEach } from "vitest";

import { useLanguage } from "@/shared/i18n/language";
import { server } from "@/test/server";

// jsdom has no scrolling; the router's scroll restoration calls it on each navigation.
window.scrollTo = () => undefined;

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
// Most tests read the Portuguese texts; the language tests choose English themselves.
beforeEach(() => useLanguage.setState({ language: "pt" }));
afterEach(() => {
  // Toasts live in a module-wide store: one test's messages must not reach the next.
  toast.dismiss();
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());

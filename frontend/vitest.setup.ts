import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { toast } from "sonner";
import { afterAll, afterEach, beforeAll } from "vitest";

import { server } from "@/test/server";

// jsdom has no scrolling; the router's scroll restoration calls it on each navigation.
window.scrollTo = () => undefined;

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => {
  // Toasts live in a module-wide store: one test's messages must not reach the next.
  toast.dismiss();
  cleanup();
  server.resetHandlers();
});
afterAll(() => server.close());

import type { QueryClient } from "@tanstack/react-query";
import {
  createRootRouteWithContext,
  createRoute,
  createRouter,
  redirect,
  type RouterHistory,
} from "@tanstack/react-router";
import { z } from "zod";

import { AppShell } from "@/app-shell";
import { sessionQuery } from "@/entities/session/session-query";
import { resultFiltersSchema } from "@/entities/result/result-filters";
import { InvoicePage } from "@/pages/invoice-page";
import { JobPage } from "@/pages/job-page";
import { LineReviewPage } from "@/pages/line-review-page";
import { LoginPage } from "@/pages/login-page";
import { ResultsPage } from "@/pages/results-page";
import { UploadPage } from "@/pages/upload-page";
import { isUnauthenticated } from "@/shared/api/errors";

import { RootLayout } from "./root-layout";

interface RouterContext {
  queryClient: QueryClient;
}

const rootRoute = createRootRouteWithContext<RouterContext>()({ component: RootLayout });

const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/login",
  component: LoginPage,
});

// Every page but login: the server decides whether there is a session (SEC-06).
const appRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: "_app",
  beforeLoad: async ({ context }) => {
    try {
      await context.queryClient.ensureQueryData(sessionQuery);
    } catch (error) {
      if (isUnauthenticated(error)) {
        throw redirect({ to: "/login" });
      }
      throw error;
    }
  },
  component: AppShell,
});

const uploadRoute = createRoute({
  getParentRoute: () => appRoute,
  path: "/",
  component: UploadPage,
});

// Jobs whose files were already uploaded; an invalid value falls back to none.
const jobSearch = z.object({ already: z.array(z.string()).optional().catch(undefined) });

const jobRoute = createRoute({
  getParentRoute: () => appRoute,
  path: "/jobs/$jobId",
  validateSearch: jobSearch,
  component: JobPage,
});

const resultsRoute = createRoute({
  getParentRoute: () => appRoute,
  path: "/jobs/$jobId/results",
  validateSearch: resultFiltersSchema,
  component: ResultsPage,
});

const invoiceRoute = createRoute({
  getParentRoute: () => appRoute,
  path: "/invoices/$invoiceId",
  component: InvoicePage,
});

const lineReviewRoute = createRoute({
  getParentRoute: () => appRoute,
  path: "/invoices/$invoiceId/lines/$lineId",
  component: LineReviewPage,
});

const routeTree = rootRoute.addChildren([
  loginRoute,
  appRoute.addChildren([uploadRoute, jobRoute, resultsRoute, invoiceRoute, lineReviewRoute]),
]);

export function createAppRouter(queryClient: QueryClient, history?: RouterHistory) {
  return createRouter({
    routeTree,
    context: { queryClient },
    ...(history === undefined ? {} : { history }),
  });
}

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof createAppRouter>;
  }
}

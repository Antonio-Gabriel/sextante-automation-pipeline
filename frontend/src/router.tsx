import type { QueryClient } from "@tanstack/react-query";
import {
  createRootRouteWithContext,
  createRoute,
  createRouter,
  redirect,
  type RouterHistory,
} from "@tanstack/react-router";

import { sessionQuery } from "@/entities/session/session-query";
import { HomePage } from "@/pages/home-page";
import { LoginPage } from "@/pages/login-page";
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

// The server decides whether there is a session (SEC-06); the page only asks.
const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
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
  component: HomePage,
});

const routeTree = rootRoute.addChildren([loginRoute, homeRoute]);

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

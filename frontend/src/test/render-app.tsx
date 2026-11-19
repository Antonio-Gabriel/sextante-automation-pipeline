import { createMemoryHistory } from "@tanstack/react-router";
import { render } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "@/app";
import { createQueryClient } from "@/query-client";
import { createAppRouter } from "@/router";

/** The whole application at one path, against the simulated API. */
export function renderApp(path: string) {
  const queryClient = createQueryClient();
  const router = createAppRouter(queryClient, createMemoryHistory({ initialEntries: [path] }));
  const user = userEvent.setup();
  render(<App queryClient={queryClient} router={router} />);
  return { user, router };
}

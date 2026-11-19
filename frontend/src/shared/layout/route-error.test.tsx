import { screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { sessionHandlers } from "@/test/api";
import { renderApp } from "@/test/render-app";
import { server } from "@/test/server";

describe("a page that cannot load (deploy, API unreachable behind nginx)", () => {
  // The session check is retried twice first (query-client.ts), about three seconds.
  it("says the server cannot be reached and loads the page once it can", { timeout: 15_000 }, async () => {
    let up = false;
    server.use(...sessionHandlers());
    server.use(
      http.get("/api/session", () =>
        up
          ? HttpResponse.json({ authenticated: true })
          : new HttpResponse("<html>502 Bad Gateway</html>", { status: 502, headers: { "Content-Type": "text/html" } }),
      ),
    );
    const { user } = renderApp("/jobs");

    expect(await screen.findByRole("alert", {}, { timeout: 8_000 })).toHaveTextContent("Não foi possível contactar o servidor.");
    expect(screen.getByRole("heading", { name: "Esta página não pôde ser carregada" })).toBeInTheDocument();

    up = true;
    await user.click(screen.getByRole("button", { name: "Tentar de novo" }));

    expect(await screen.findByRole("heading", { name: "Trabalhos" })).toBeInTheDocument();
  });
});

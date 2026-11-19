import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { http } from "msw";

import { apiWithoutSession, CATALOG_DIGEST, refused } from "@/test/api";
import { renderApp } from "@/test/render-app";
import { server } from "@/test/server";

const TOKEN = "synthetic-access-token-0123456789";

function withApi() {
  const api = apiWithoutSession(TOKEN);
  server.use(...api.handlers);
  return api;
}

describe("login by access token (frontend ticket 01)", () => {
  it("sends a browser without a session to the login screen", async () => {
    withApi();
    const { router } = renderApp("/");

    expect(await screen.findByLabelText("Token de acesso")).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/login");
  });

  it("opens the panel with the right token, showing the server and catalog", async () => {
    withApi();
    const { user } = renderApp("/login");

    await user.type(await screen.findByLabelText("Token de acesso"), TOKEN);
    await user.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByText(CATALOG_DIGEST.slice(0, 12))).toBeInTheDocument();
    expect(screen.getByText("Disponível")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Carregar facturas" })).toBeInTheDocument();
  });

  it("shows the server's message for a wrong token, and stays on login", async () => {
    withApi();
    const { user, router } = renderApp("/login");

    await user.type(await screen.findByLabelText("Token de acesso"), "wrong-token-of-enough-length");
    await user.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByText("Token de acesso inválido.")).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/login");
  });

  it("asks for the token before sending an empty one", async () => {
    const api = withApi();
    const { user } = renderApp("/login");

    await user.click(await screen.findByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Indique o token de acesso.");
    expect(api.calls.login).toBe(0);
  });

  it("never writes the token into browser storage", async () => {
    withApi();
    const { user } = renderApp("/login");

    await user.type(await screen.findByLabelText("Token de acesso"), TOKEN);
    await user.click(screen.getByRole("button", { name: "Entrar" }));
    await screen.findByText(CATALOG_DIGEST.slice(0, 12));

    const stored = [localStorage, sessionStorage].flatMap((storage) =>
      Object.keys(storage).map((key) => storage.getItem(key)),
    );
    expect(stored.join()).not.toContain(TOKEN);
    expect(document.cookie).not.toContain(TOKEN);
  });
});

describe("logout (frontend ticket 01)", () => {
  async function loggedIn() {
    const api = withApi();
    const rendered = renderApp("/login");
    await rendered.user.type(await screen.findByLabelText("Token de acesso"), TOKEN);
    await rendered.user.click(screen.getByRole("button", { name: "Entrar" }));
    await screen.findByText(CATALOG_DIGEST.slice(0, 12));
    return { api, ...rendered };
  }

  it("ends the session in the server and returns to login", async () => {
    const { api, user, router } = await loggedIn();

    await user.click(screen.getByRole("button", { name: "Sair" }));

    expect(await screen.findByLabelText("Token de acesso")).toBeInTheDocument();
    expect(api.calls.logout).toBe(1);
    expect(router.state.location.pathname).toBe("/login");
  });

  it("does not reopen the application after logout without the token", async () => {
    const { user, router } = await loggedIn();
    await user.click(screen.getByRole("button", { name: "Sair" }));
    await screen.findByLabelText("Token de acesso");

    await router.navigate({ to: "/" });

    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
  });
});

describe("logout the server does not confirm (frontend ticket 01)", () => {
  it("keeps the person in, with the server's message, so no session is left open unseen", async () => {
    const api = apiWithoutSession(TOKEN);
    server.use(...api.handlers);
    // A later server.use takes precedence over the handlers above.
    server.use(
      http.post("/api/session/end", () =>
        refused("errors.internal", "Ocorreu um erro interno.", 500),
      ),
    );
    const { user, router } = renderApp("/login");
    await user.type(await screen.findByLabelText("Token de acesso"), TOKEN);
    await user.click(screen.getByRole("button", { name: "Entrar" }));
    await screen.findByText(CATALOG_DIGEST.slice(0, 12));

    await user.click(screen.getByRole("button", { name: "Sair" }));

    expect(await screen.findByText("Ocorreu um erro interno.")).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/");
  });
});

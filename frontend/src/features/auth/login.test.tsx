import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { apiWithoutSession, CATALOG_DIGEST } from "@/test/api";
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

  it("opens the application with the right token, showing the server and catalog", async () => {
    withApi();
    const { user } = renderApp("/login");

    await user.type(await screen.findByLabelText("Token de acesso"), TOKEN);
    await user.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByText(CATALOG_DIGEST)).toBeInTheDocument();
    expect(screen.getByText("Disponível")).toBeInTheDocument();
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
    await screen.findByText(CATALOG_DIGEST);

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
    await screen.findByText(CATALOG_DIGEST);
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

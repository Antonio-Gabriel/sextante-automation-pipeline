import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { refused, resultLine, sessionHandlers } from "@/test/api";
import type { components } from "@/shared/api/schema";
import { renderApp } from "@/test/render-app";
import { server } from "@/test/server";

const JOB = "job-0001-aaaa";
const PATH = `/jobs/${JOB}/results`;

/** Answers every results request with these lines, and records the query it got. */
function withResults(
  lines: components["schemas"]["ResultLineResponse"][],
  page: { limit?: number; truncated?: boolean } = {}) {
  const queries: URLSearchParams[] = [];
  server.use(
    ...sessionHandlers(),
    http.get("/api/jobs/:jobId/results", ({ request }) => {
      const query = new URL(request.url).searchParams;
      queries.push(query);
      return HttpResponse.json({
        lines,
        limit: page.limit ?? 100,
        offset: Number(query.get("offset") ?? 0),
        limit_truncated: page.truncated ?? false,
      });
    }),
  );
  return { last: () => queries.at(-1) };
}

describe("results with filters (frontend ticket 03)", () => {
  it("shows each line with its decision, flags and notes as the API's Portuguese text", async () => {
    withResults([
      resultLine(1, {
        confidence: "LOW",
        flags: [{ code: "no_match", message: "Sem correspondência no catálogo." }],
        notes: [{ code: "generic_item", message: "Item genérico escolhido." }],
        review_note: "<b>not markup</b>",
      }),
    ]);
    renderApp(PATH);

    const row = (await screen.findByText("Synthetic service 1")).closest("tr");
    expect(row).not.toBeNull();
    const cells = within(row ?? document.body);
    expect(cells.getByText("Baixa")).toBeInTheDocument();
    expect(cells.getByText("Sem correspondência no catálogo.")).toBeInTheDocument();
    expect(cells.getByText("Item genérico escolhido.")).toBeInTheDocument();
    expect(cells.getByText("<b>not markup</b>")).toBeInTheDocument();
    expect(cells.getByText("Sim")).toBeInTheDocument();
  });

  it.each([
    ["Confiança", "LOW", "confidence", "LOW", "confidence=LOW"],
    ["Aba", "OUTLAYS", "target_sheet", "OUTLAYS", "sheet=OUTLAYS"],
    ["Sinalização", "true", "flagged", "true", "flagged=true"],
    ["Sinalização", "false", "flagged", "false", "flagged=false"],
  ])("filters by %s, in the request and in the address", async (label, option, param, sent, inAddress) => {
    const api = withResults([resultLine(1)]);
    const { user, router } = renderApp(PATH);
    await screen.findByText("Synthetic service 1");

    await user.selectOptions(screen.getByLabelText(label), option);

    await screen.findByText("Synthetic service 1");
    expect(api.last()?.get(param)).toBe(sent);
    expect(router.state.location.href).toContain(inAddress);
  });

  it("filters by invoice from a row, and clears that filter", async () => {
    const api = withResults([resultLine(1)]);
    const { user } = renderApp(PATH);
    await screen.findByText("Synthetic service 1");

    await user.click(screen.getByRole("button", { name: "Filtrar pela factura FT 2026/17" }));
    await screen.findByRole("button", { name: "Mostrar todas as facturas" });
    expect(screen.getByText("Só a factura FT 2026/17")).toBeInTheDocument();
    expect(api.last()?.get("invoice_id")).toBe("inv-1");

    await user.click(screen.getByRole("button", { name: "Mostrar todas as facturas" }));
    await screen.findByText("Synthetic service 1");
    expect(api.last()?.get("invoice_id")).toBeNull();
  });

  it("drops an invalid filter of the address and keeps the valid ones", async () => {
    const api = withResults([resultLine(1)]);
    renderApp(`${PATH}?confidence=SURE&sheet=OUTLAYS`);
    await screen.findByText("Synthetic service 1");

    expect(api.last()?.get("confidence")).toBeNull();
    expect(api.last()?.get("target_sheet")).toBe("OUTLAYS");
    expect(screen.getByLabelText("Confiança")).toHaveValue("");
  });

  it("says the server cut the page, and pages with the server's limit", async () => {
    const lines = Array.from({ length: 100 }, (_, n) => resultLine(n + 1));
    const api = withResults(lines, { limit: 100, truncated: true });
    const { user } = renderApp(`${PATH}?limit=500`);

    expect(await screen.findByText(/no máximo 100 linhas por página/)).toBeInTheDocument();
    expect(screen.getByText("Linhas 1 a 100")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Seguinte" }));
    await screen.findByText("Linhas 101 a 200");
    expect(api.last()?.get("offset")).toBe("100");
  });

  it("leads from a line to its review and from an invoice to its screen", async () => {
    withResults([resultLine(3)]);
    renderApp(PATH);

    expect(await screen.findByRole("link", { name: "Synthetic service 3" })).toHaveAttribute(
      "href",
      "/invoices/inv-1/lines/line-3",
    );
    expect(screen.getByRole("link", { name: "FT 2026/17" })).toHaveAttribute("href", "/invoices/inv-1");
  });

  it("says how to open each line: a review button when pending, and the whole row", async () => {
    withResults([resultLine(3, { review_status: "pending" }), resultLine(4, { review_status: "accepted" })]);
    const { user, router } = renderApp(PATH);

    expect(await screen.findByRole("link", { name: "Rever a linha 3" })).toHaveTextContent("Rever");
    expect(screen.getByRole("link", { name: "Abrir a linha 4" })).toHaveTextContent("Abrir");

    await user.click(screen.getByText("Synthetic service 4").closest("tr")?.querySelector("td") ?? document.body);
    expect(router.state.location.pathname).toBe("/invoices/inv-1/lines/line-4");
  });

  it("a click on the filter of a row filters, it does not open the line", async () => {
    withResults([resultLine(1)]);
    const { user, router } = renderApp(PATH);
    await screen.findByText("Synthetic service 1");

    await user.click(screen.getByRole("button", { name: "Filtrar pela factura FT 2026/17" }));

    expect(router.state.location.pathname).toBe(PATH);
  });

  it("drops an invalid page position of the address", async () => {
    const api = withResults([resultLine(1)]);
    renderApp(`${PATH}?offset=-5&limit=0`);
    await screen.findByText("Synthetic service 1");

    expect(api.last()?.get("offset")).toBe("0");
    expect(api.last()?.get("limit")).toBeNull();
  });

  it("past the last line, says so and keeps the way back", async () => {
    const api = withResults([]);
    const { user } = renderApp(`${PATH}?offset=100`);

    expect(await screen.findByText("Não há mais linhas depois desta página.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Anterior" }));

    await screen.findByText("Nenhuma linha com estes filtros.");
    expect(api.last()?.get("offset")).toBe("0");
  });

  it("shows the server's message when the results cannot be read", async () => {
    server.use(
      ...sessionHandlers(),
      http.get("/api/jobs/:jobId/results", () =>
        refused("errors.job.not_found", "Trabalho não encontrado.", 404),
      ),
    );
    renderApp(PATH);

    expect(await screen.findByRole("alert")).toHaveTextContent("Trabalho não encontrado.");
    expect(screen.queryByText("Nenhuma linha com estes filtros.")).not.toBeInTheDocument();
  });
});

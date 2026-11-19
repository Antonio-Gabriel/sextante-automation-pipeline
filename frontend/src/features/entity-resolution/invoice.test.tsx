import { screen, waitFor } from "@testing-library/react";
import { delay, http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { components as openapiComponents } from "../../../openapi.json";
import { RESOLUTIONS } from "@/entities/invoice/entity-resolutions";
import { invoiceView, refused, resultLine, sessionHandlers } from "@/test/api";
import { renderApp } from "@/test/render-app";
import { server } from "@/test/server";

const PATH = "/invoices/inv-1";

const AMBIGUOUS = invoiceView({
  status: "not_coded",
  entity_verdict: "AMBIGUOUS",
  entity_reason: { code: "entity_similar_not_equal", message: "Entidade parecida com a AMT, mas não igual: confirmar." },
  resolvable: true,
  target_sheet: null,
});

interface Sent {
  key: string | null;
  body: unknown;
}

/** The invoice and its lines; the resolution answers with `answer` and records each send. */
function withInvoice(
  invoice = AMBIGUOUS,
  answer: () => Promise<Response> | Response = () => accepted(),
  lineCount = 1,
) {
  const sent: Sent[] = [];
  server.use(
    ...sessionHandlers(),
    http.get("/api/invoices/:invoiceId", () => HttpResponse.json(invoice)),
    http.get("/api/jobs/:jobId/results", () =>
      HttpResponse.json({
        lines: Array.from({ length: lineCount }, (_, n) => resultLine(n + 1)),
        limit: 100,
        offset: 0,
        limit_truncated: false,
      }),
    ),
    http.post("/api/invoices/:invoiceId/entity-resolution", async ({ request }) => {
      sent.push({ key: request.headers.get("Idempotency-Key"), body: await request.json() });
      return answer();
    }),
  );
  return sent;
}

function accepted() {
  return HttpResponse.json({ invoice_id: "inv-1", job_id: "job-0001-aaaa" }, { status: 202 });
}

describe("invoice screen and entity resolution (frontend ticket 05)", () => {
  it("shows the extracted header, the entity decision and the lines", async () => {
    withInvoice(invoiceView());
    renderApp(PATH);

    expect(await screen.findByRole("heading", { name: "Factura FT 2026/17" })).toBeInTheDocument();
    expect(screen.getByText("Corresponde à AMT")).toBeInTheDocument();
    expect(screen.getByText("AOA")).toBeInTheDocument();
    expect(await screen.findByText("Synthetic service 1")).toBeInTheDocument();
    expect(screen.queryByText("Resolução da entidade")).not.toBeInTheDocument();
  });

  it("shows why the entity is ambiguous, and offers the resolution", async () => {
    withInvoice();
    renderApp(PATH);

    expect(await screen.findByText("Entidade parecida com a AMT, mas não igual: confirmar.")).toBeInTheDocument();
    expect(screen.getByText("Ambígua: precisa de resolução")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Resolver e codificar" })).toBeInTheDocument();
  });

  it("requires a decision and a note before sending", async () => {
    const sent = withInvoice();
    const { user } = renderApp(PATH);

    await user.click(await screen.findByRole("button", { name: "Resolver e codificar" }));

    expect(await screen.findByText("Escreva uma nota a justificar a decisão.")).toBeInTheDocument();
    expect(screen.getByText("Escolha uma decisão.")).toBeInTheDocument();
    expect(sent).toEqual([]);
  });

  it("sends the resolution with its Idempotency-Key, once, and counts the note", async () => {
    const sent = withInvoice(AMBIGUOUS, async () => {
      await delay(200);
      return accepted();
    });
    const { user } = renderApp(PATH);

    await user.click(await screen.findByLabelText("Não é a AMT"));
    await user.type(screen.getByLabelText("Nota (obrigatória)"), "Empresa irmã.");
    expect(screen.getByText("Restam 487 caracteres.")).toBeInTheDocument();
    const submit = screen.getByRole("button", { name: "Resolver e codificar" });
    await user.click(submit);
    await user.click(submit);

    expect(await screen.findByText(/Entidade resolvida/)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("heading", { name: "Entidade" })).toHaveFocus());
    expect(sent).toHaveLength(1);
    expect(sent[0]?.body).toEqual({ resolution: "NO_MATCH", note: "Empresa irmã." });
    expect(sent[0]?.key).toMatch(/^[0-9a-f-]{36}$/);
  });

  it("shows the server's refusal and keeps the same key for the retry", async () => {
    let first = true;
    const sent = withInvoice(AMBIGUOUS, () => {
      if (first) {
        first = false;
        return refused("errors.internal", "Ocorreu um erro interno.", 500);
      }
      return accepted();
    });
    const { user } = renderApp(PATH);
    await user.click(await screen.findByLabelText("É a AMT"));
    await user.type(screen.getByLabelText("Nota (obrigatória)"), "Confirmado.");

    await user.click(screen.getByRole("button", { name: "Resolver e codificar" }));
    expect(await screen.findByText("Ocorreu um erro interno.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Resolver e codificar" }));

    await waitFor(() => expect(sent).toHaveLength(2));
    expect(sent[1]?.key).toBe(sent[0]?.key);
  });

  it("names the earlier invoice of a possible duplicate, with a link to it", async () => {
    withInvoice(invoiceView({ possible_duplicate_of: { invoice_id: "inv-0", invoice_number: "FT 2026/16" } }));
    renderApp(PATH);

    expect(await screen.findByText("Possível duplicado da factura FT 2026/16.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Abrir a factura anterior" })).toHaveAttribute("href", "/invoices/inv-0");
  });

  it("says so when the invoice does not exist", async () => {
    server.use(
      ...sessionHandlers(),
      http.get("/api/invoices/:invoiceId", () => refused("errors.invoice.not_found", "Factura não encontrada.", 404)),
    );
    renderApp("/invoices/missing");

    expect(await screen.findByText("Esta factura não existe.")).toBeInTheDocument();
  });

  it("hides the form once resolved, and shows the recorded resolution", async () => {
    withInvoice(
      invoiceView({
        entity_verdict: "NO_MATCH",
        target_sheet: "OUTLAYSP",
        entity_resolution: { verdict: "NO_MATCH", note: "Empresa irmã.", resolved_at: "2026-11-19T09:00:00+00:00" },
      }),
    );
    renderApp(PATH);

    expect(await screen.findByText("Resolvida pelo revisor: Não é a AMT")).toBeInTheDocument();
    expect(screen.getByText("Empresa irmã.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Resolver e codificar" })).not.toBeInTheDocument();
  });

  it("offers exactly the resolutions of the OpenAPI contract", () => {
    const contract = openapiComponents.schemas.EntityResolutionRequest.properties.resolution.enum;
    expect([...RESOLUTIONS]).toEqual(contract);
  });

  it("says when the invoice has more lines than the page shows", async () => {
    withInvoice(invoiceView(), () => accepted(), 100);
    renderApp(PATH);

    expect(await screen.findByText(/mais linhas do que as mostradas/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ver todas no ecrã de resultados" })).toHaveAttribute(
      "href",
      "/jobs/job-0001-aaaa/results?invoice=inv-1",
    );
  });

  it("takes a new key after the server says the key was used for another request", async () => {
    let first = true;
    const sent = withInvoice(AMBIGUOUS, () => {
      if (!first) return accepted();
      first = false;
      return refused("errors.idempotency.key_reused", "A chave Idempotency-Key já foi usada noutro pedido.", 422);
    });
    const { user } = renderApp(PATH);
    await user.click(await screen.findByLabelText("É a AMT"));
    await user.type(screen.getByLabelText("Nota (obrigatória)"), "Confirmado.");

    await user.click(screen.getByRole("button", { name: "Resolver e codificar" }));
    await screen.findByText("A chave Idempotency-Key já foi usada noutro pedido.");
    await user.click(screen.getByRole("button", { name: "Resolver e codificar" }));

    await waitFor(() => expect(sent).toHaveLength(2));
    expect(sent[1]?.key).not.toBe(sent[0]?.key);
  });
});

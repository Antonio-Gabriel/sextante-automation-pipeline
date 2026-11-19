import { screen, waitFor, within } from "@testing-library/react";
import { delay, http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import type { components } from "@/shared/api/schema";
import { invoiceView, refused, resultLine, sessionHandlers } from "@/test/api";
import { renderApp } from "@/test/render-app";
import { server } from "@/test/server";

type ResultLine = components["schemas"]["ResultLineResponse"];
type Coding = components["schemas"]["CodingHistoryResponse"];

const PATH = "/invoices/inv-1/lines/line-1";

const CANDIDATES = [
  { rank: 1, item_number: "O00004", description_pt: "Passagens aéreas", description_en: "Air tickets", score: 0.912, chosen_by_model: true },
  { rank: 2, item_number: "O00007", description_pt: "Alojamento", description_en: "Lodging", score: 0.401, chosen_by_model: false },
];

const CODING: Coding = {
  encoded_line_id: "coded-1",
  in_force: true,
  encoded_at: "2026-11-19T09:00:00+00:00",
  superseded_at: null,
  item_number: "O00004",
  catalog_description: "Passagens aéreas",
  confidence: "HIGH",
  prompt_version: "item-choice-v2",
  model_id: "claude-sonnet-5-5",
  catalog_digest: "739ca559901d5731b65af269606591c9",
  review: null,
};

interface Sent {
  method: string;
  key: string | null;
  body: unknown;
}

/** The line, its sheet's items and history; the review endpoints answer with `answer`. */
function withLine(
  line: Partial<ResultLine> = {},
  options: { sheet?: string | null; history?: Coding[]; answer?: () => Promise<Response> | Response } = {},
) {
  const sent: Sent[] = [];
  const sheet = options.sheet === undefined ? "OUTLAYS" : options.sheet;
  const record = async (method: string, request: Request) => {
    sent.push({ method, key: request.headers.get("Idempotency-Key"), body: await request.json() });
    return options.answer?.() ?? HttpResponse.json({ encoded_line_id: "coded-1", review_status: "accepted", confidence: "HIGH", item_number: "O00004", catalog_description: null, review_note: null, target_sheet: sheet });
  };
  server.use(
    ...sessionHandlers(),
    http.get("/api/invoices/:invoiceId", () => HttpResponse.json(invoiceView())),
    http.get("/api/jobs/:jobId/results", () =>
      HttpResponse.json({ lines: [resultLine(1, { target_sheet: sheet, ...line })], limit: 100, offset: 0, limit_truncated: false }),
    ),
    http.get("/api/invoices/:invoiceId/lines/:lineId/candidates", () =>
      HttpResponse.json({ target_sheet: sheet, candidates: sheet === null ? [] : CANDIDATES }),
    ),
    http.get("/api/invoices/:invoiceId/lines/:lineId/history", () => HttpResponse.json(options.history ?? [CODING])),
    http.post("/api/encoded-lines/:id/accept", ({ request }) => record("accept", request)),
    http.patch("/api/encoded-lines/:id", ({ request }) => record("correct", request)),
  );
  return sent;
}

describe("line review (frontend ticket 04)", () => {
  it("lists every item of the line's sheet with rank, score and the model's choice", async () => {
    withLine();
    renderApp(PATH);

    const table = await screen.findByRole("table");
    const rows = within(table).getAllByRole("row");
    expect(rows).toHaveLength(3);
    expect(within(rows[1] ?? table).getByText("Escolha do modelo")).toBeInTheDocument();
    expect(within(rows[1] ?? table).getByText("0,912")).toBeInTheDocument();
    expect(within(rows[2] ?? table).getByText("Alojamento")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Itens da aba OUTLAYS" })).toBeInTheDocument();
  });

  it("accepts a pending line with its note, once, with an Idempotency-Key", async () => {
    const sent = withLine({}, {
      answer: async () => {
        await delay(150);
        return HttpResponse.json({ encoded_line_id: "coded-1", review_status: "accepted", confidence: "HIGH", item_number: "O00004", catalog_description: null, review_note: "Ok", target_sheet: "OUTLAYS" });
      },
    });
    const { user } = renderApp(PATH);

    await user.type(await screen.findByLabelText("Nota (opcional)"), "Ok");
    expect(screen.getByText("Restam 498 caracteres.")).toBeInTheDocument();
    const accept = screen.getByRole("button", { name: "Aceitar a linha" });
    await user.click(accept);
    await user.click(accept);

    expect(await screen.findByText("Linha aceite.")).toBeInTheDocument();
    expect(sent).toHaveLength(1);
    expect(sent[0]).toMatchObject({ method: "accept", body: { note: "Ok" } });
    expect(sent[0]?.key).toMatch(/^[0-9a-f-]{36}$/);
  });

  it("corrects the code to an item chosen from the sheet", async () => {
    const sent = withLine();
    const { user } = renderApp(PATH);

    await user.click(await screen.findByRole("radio", { name: "Escolher O00007 para a correcção" }));
    await user.click(screen.getByRole("button", { name: "Corrigir para O00007" }));

    expect(await screen.findByText("Código corrigido.")).toBeInTheDocument();
    expect(sent[0]).toMatchObject({ method: "correct", body: { item_number: "O00007", note: null } });
  });

  it("shows the server's refusal of a correction", async () => {
    withLine({}, { answer: () => refused("errors.review.item_not_in_sheet", "O item escolhido não pertence à aba de destino da linha.", 422) });
    const { user } = renderApp(PATH);

    await user.click(await screen.findByRole("radio", { name: "Escolher O00007 para a correcção" }));
    await user.click(screen.getByRole("button", { name: "Corrigir para O00007" }));

    expect(await screen.findByText("O item escolhido não pertence à aba de destino da linha.")).toBeInTheDocument();
  });

  it("offers acceptance only to a pending line", async () => {
    withLine({ review_status: "accepted" });
    renderApp(PATH);

    expect(await screen.findByText(/já foi revista/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Aceitar a linha" })).not.toBeInTheDocument();
  });

  it("offers no correction to a line without a sheet, and says why", async () => {
    withLine({ item_number: null }, { sheet: null });
    renderApp(PATH);

    expect(await screen.findByText(/resolva primeiro a entidade da factura/)).toBeInTheDocument();
    expect(screen.queryByRole("radio")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Abrir a factura" })).toHaveAttribute("href", "/invoices/inv-1");
  });

  it("shows each coding, in force or superseded, with prompt, catalog and review", async () => {
    withLine({}, {
      history: [
        CODING,
        { ...CODING, encoded_line_id: "coded-0", in_force: false, superseded_at: "2026-11-19T09:00:00+00:00", item_number: "O00007", prompt_version: "item-choice-v1", review: { review_status: "corrected", item_number: "O00007", note: "Era alojamento." } },
      ],
    });
    renderApp(PATH);

    expect(await screen.findByText("Substituída")).toBeInTheDocument();
    expect(screen.getByText("item-choice-v1")).toBeInTheDocument();
    expect(screen.getByText("Era alojamento.")).toBeInTheDocument();
    expect(screen.getAllByText("739ca559901d")).toHaveLength(2);
    await waitFor(() => expect(screen.getByText("Corrigida")).toBeInTheDocument());
  });
});

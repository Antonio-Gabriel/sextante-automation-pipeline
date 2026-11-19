import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";

import { fileNameOf } from "@/features/export/use-export";
import { invoiceView, refused, resultLine, sessionHandlers } from "@/test/api";
import { renderApp } from "@/test/render-app";
import { server } from "@/test/server";

const JOB = "job-0001-aaaa";

function withLines() {
  return http.get("/api/jobs/:jobId/results", () =>
    HttpResponse.json({ lines: [resultLine(1)], limit: 100, offset: 0, limit_truncated: false }),
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("export (frontend ticket 06)", () => {
  it.each(["csv", "xlsx"])("downloads the %s file the server made, with the session", async (format) => {
    const formats: (string | null)[] = [];
    server.use(
      ...sessionHandlers(),
      withLines(),
      http.get("/api/exports/:jobId", ({ request }) => {
        formats.push(new URL(request.url).searchParams.get("format"));
        return new HttpResponse("Invoice_ID,Item\n", {
          headers: { "Content-Disposition": `attachment; filename="sextante-${JOB}.${format}"` },
        });
      }),
    );
    const createUrl = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:export");
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
    const saved: string[] = [];
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(function (this: HTMLAnchorElement) {
      saved.push(this.download);
    });
    const { user } = renderApp(`/jobs/${JOB}/results`);

    await user.click(await screen.findByRole("button", { name: `Exportar ${format.toUpperCase()}` }));

    expect(await screen.findByText("Exportação descarregada.")).toBeInTheDocument();
    expect(formats).toEqual([format]);
    expect(createUrl).toHaveBeenCalledOnce();
    expect(saved).toEqual([`sextante-${JOB}.${format}`]);
  });

  it("shows the server's refusal instead of saving an error as a file", async () => {
    server.use(
      ...sessionHandlers(),
      withLines(),
      http.get("/api/exports/:jobId", () =>
        refused("errors.rate_limit.exceeded", "Pedidos a mais em pouco tempo. Tente de novo mais tarde.", 429),
      ),
    );
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    const { user } = renderApp(`/jobs/${JOB}/results`);

    await user.click(await screen.findByRole("button", { name: "Exportar CSV" }));

    expect(await screen.findByText(/Pedidos a mais/)).toBeInTheDocument();
    expect(click).not.toHaveBeenCalled();
  });

  it("reads the file name from the server's header", () => {
    expect(fileNameOf('attachment; filename="sextante-j1.xlsx"')).toBe("sextante-j1.xlsx");
    expect(fileNameOf(null)).toBe("sextante-export");
  });
});

describe("reprocessing (frontend ticket 06)", () => {
  function withInvoice(status: string, answer: () => Response = () => accepted()) {
    const keys: (string | null)[] = [];
    server.use(
      ...sessionHandlers(),
      withLines(),
      http.get("/api/invoices/:invoiceId", () => HttpResponse.json(invoiceView({ status }))),
      http.post("/api/invoices/:invoiceId/reprocess", ({ request }) => {
        keys.push(request.headers.get("Idempotency-Key"));
        return answer();
      }),
    );
    return keys;
  }

  function accepted() {
    return HttpResponse.json({ invoice_id: "inv-1", job_id: JOB }, { status: 202 });
  }

  it("asks for confirmation, warning that the coding is replaced and reviews reopen", async () => {
    const keys = withInvoice("encoded");
    const { user } = renderApp("/invoices/inv-1");

    await user.click(await screen.findByRole("button", { name: "Reprocessar a factura" }));

    const dialog = screen.getByRole("alertdialog", { name: "Reprocessar esta factura?" });
    expect(dialog).toHaveAccessibleDescription(/fica substituída .* voltam à revisão/);
    expect(screen.getByRole("button", { name: "Sim, reprocessar" })).toHaveFocus();
    expect(keys).toEqual([]);

    await user.click(screen.getByRole("button", { name: "Sim, reprocessar" }));

    expect(await screen.findByText(/voltou à fila/)).toBeInTheDocument();
    expect(keys).toHaveLength(1);
    expect(keys[0]).toMatch(/^[0-9a-f-]{36}$/);
  });

  it("cancels without sending anything", async () => {
    const keys = withInvoice("failed");
    const { user } = renderApp("/invoices/inv-1");

    await user.click(await screen.findByRole("button", { name: "Reprocessar a factura" }));
    await user.click(screen.getByRole("button", { name: "Cancelar" }));

    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(keys).toEqual([]);
  });

  it.each(["rejected", "not_coded", "queued"])("is not offered to an invoice that is %s", async (status) => {
    withInvoice(status);
    renderApp("/invoices/inv-1");

    await screen.findByRole("heading", { name: "Factura FT 2026/17" });
    expect(screen.queryByRole("button", { name: "Reprocessar a factura" })).not.toBeInTheDocument();
  });

  it("shows the server's refusal of an invoice that cannot be reprocessed", async () => {
    withInvoice("encoded", () =>
      refused("errors.invoice.not_reprocessable", "Só uma factura com falha ou já codificada pode ser reprocessada.", 409),
    );
    const { user } = renderApp("/invoices/inv-1");

    await user.click(await screen.findByRole("button", { name: "Reprocessar a factura" }));
    await user.click(screen.getByRole("button", { name: "Sim, reprocessar" }));

    expect(await screen.findByText(/Só uma factura com falha/)).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument());
  });
});

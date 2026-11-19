import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";

import { pollingInterval } from "@/entities/job/use-job-progress";
import { jobProgress, refused, sessionHandlers } from "@/test/api";
import { renderApp } from "@/test/render-app";
import { server } from "@/test/server";

const JOB = "job-0001-aaaa";

function pdf(name: string) {
  return new File(["%PDF-1.7 synthetic"], name, { type: "application/pdf" });
}

/** The upload answers with this receipt; the job then answers each poll in turn. */
function withUpload(receipt: object, polls: object[]) {
  const received: number[] = [];
  let poll = 0;
  server.use(
    ...sessionHandlers(),
    http.post("/api/invoices", async ({ request }) => {
      const form = await request.formData();
      // jsdom's FormData loses the part names on the way through Node's fetch, so the test
      // counts the parts; the names were checked against the real server.
      received.push(form.getAll("files").length);
      return HttpResponse.json(receipt, { status: 202 });
    }),
    http.get("/api/jobs/:jobId", () => {
      const answer = polls[Math.min(poll, polls.length - 1)];
      poll += 1;
      return HttpResponse.json(answer);
    }),
  );
  return { received, polls: () => poll };
}

async function uploadFiles(...names: string[]) {
  const rendered = renderApp("/");
  await rendered.user.upload(await screen.findByLabelText("Ficheiros a carregar"), names.map(pdf));
  await rendered.user.click(screen.getByRole("button", { name: /^Carregar \d+ ficheiros?$/ }));
  return rendered;
}

const receipt = (jobId: string, existing: string[] = []) => ({
  job_id: jobId,
  status: "queued",
  invoice_count: 2,
  existing_job_ids: existing,
  restored_job_ids: [],
});

afterEach(() => {
  vi.useRealTimers();
});

describe("upload with progress (frontend ticket 02)", () => {
  it("sends the chosen PDFs and follows the job until it finishes, then leads to results", async () => {
    const api = withUpload(receipt(JOB), [
      jobProgress(JOB, "running", { queued: 1, encoded: 1 }),
      jobProgress(JOB, "completed", { encoded: 1, rejected: 1 }),
    ]);
    const { router } = await uploadFiles("a.pdf", "b.pdf");

    expect(await screen.findByRole("link", { name: /Ver resultados/ })).toBeInTheDocument();
    expect(api.received).toEqual([2]);
    expect(router.state.location.pathname).toBe(`/jobs/${JOB}`);
    expect(screen.getByText("Concluído")).toBeInTheDocument();
    expect(screen.getByText("2/2 facturas tratadas")).toBeInTheDocument();
    // Portuguese grouping: a (narrow) space between thousands.
    expect(screen.getByText(/^12\s500 \/ 80$/)).toBeInTheDocument();
  });

  it("shows the server's refusal in Portuguese and stays on the upload screen", async () => {
    server.use(
      ...sessionHandlers(),
      http.post("/api/invoices", () =>
        refused("errors.upload.too_large", "O ficheiro excede o tamanho máximo permitido.", 413),
      ),
    );
    const { router } = await uploadFiles("big.pdf");

    expect(await screen.findByText("O ficheiro excede o tamanho máximo permitido.")).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/");
  });

  it("shows the existing job of files already uploaded, without treating it as an error", async () => {
    withUpload(receipt(JOB, [JOB]), [jobProgress(JOB, "completed", { encoded: 2 })]);
    await uploadFiles("a.pdf");

    expect(await screen.findByText(/nenhum trabalho novo foi criado/)).toBeInTheDocument();
  });

  it("links to the other jobs when only some files were already uploaded", async () => {
    withUpload(receipt(JOB, ["job-0000-old1"]), [jobProgress(JOB, "queued", { queued: 1 })]);
    await uploadFiles("a.pdf", "b.pdf");

    expect(await screen.findByRole("link", { name: "job-0000" })).toHaveAttribute("href", "/jobs/job-0000-old1");
  });

  it("says no job was created when every file was already in earlier jobs", async () => {
    withUpload(receipt(JOB, [JOB, "job-0000-old1"]), [jobProgress(JOB, "completed", { encoded: 2 })]);
    await uploadFiles("a.pdf", "b.pdf");

    expect(await screen.findByText(/nenhum trabalho novo foi criado/)).toBeInTheDocument();
    expect(screen.getByText("Outros ficheiros deste envio estão em:")).toBeInTheDocument();
    expect(screen.queryByText(/não foram repetidos/)).not.toBeInTheDocument();
  });

  it("stops polling once the job is finished", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const api = withUpload(receipt(JOB), [jobProgress(JOB, "completed", { encoded: 2 })]);
    await uploadFiles("a.pdf");
    await screen.findByText("Concluído");
    const after = api.polls();

    await vi.advanceTimersByTimeAsync(60_000);

    expect(api.polls()).toBe(after);
  });

  it("stops polling a job that does not exist, and says so", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let polls = 0;
    server.use(
      ...sessionHandlers(),
      http.get("/api/jobs/:jobId", () => {
        polls += 1;
        return refused("errors.job.not_found", "Trabalho não encontrado.", 404);
      }),
    );
    renderApp("/jobs/job-missing");
    expect(await screen.findByText("Este trabalho não existe.")).toBeInTheDocument();

    await vi.advanceTimersByTimeAsync(60_000);

    expect(polls).toBe(1);
  });

  it("polls a running job less and less often, up to five seconds", () => {
    expect([0, 1, 2, 10].map(pollingInterval)).toEqual([500, 750, 1125, 5000]);
  });

  it("ignores an invalid list of earlier jobs in the address", async () => {
    withUpload(receipt(JOB), [jobProgress(JOB, "completed", { encoded: 1 })]);
    renderApp(`/jobs/${JOB}?already=7`);

    await screen.findByText("Concluído");
    await waitFor(() => expect(screen.queryByRole("status")).not.toBeInTheDocument());
  });
});

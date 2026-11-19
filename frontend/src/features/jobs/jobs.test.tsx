import { screen, waitFor, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { jobEntry, jobList, jobProgress, refused, sessionHandlers } from "@/test/api";
import { renderApp } from "@/test/render-app";
import { server } from "@/test/server";

const DONE = "job-done-0001";
const RUNNING = "job-runs-0002";

/** The server's jobs; a DELETE removes one, and records the key it came with. */
function withJobs(jobs = [jobEntry(DONE, "completed", { encoded: 2, rejected: 1 }), jobEntry(RUNNING, "running", { queued: 1 })]) {
  let listed = [...jobs];
  const keys: (string | null)[] = [];
  // A later use() comes first: these answers replace the empty list of sessionHandlers.
  server.use(...sessionHandlers());
  server.use(
    http.get("/api/jobs", () => HttpResponse.json(jobList(listed))),
    http.delete("/api/jobs/:jobId", ({ request, params }) => {
      keys.push(request.headers.get("Idempotency-Key"));
      listed = listed.filter((job) => job.job_id !== params.jobId);
      return HttpResponse.json({ job_id: params.jobId });
    }),
  );
  return { keys };
}

describe("list and delete jobs (frontend ticket 07)", () => {
  it("lists the jobs with their date, status and invoices; only finished ones can be deleted", async () => {
    withJobs();
    renderApp("/jobs");

    const done = (await screen.findByRole("link", { name: "job-done" })).closest("tr");
    const running = screen.getByRole("link", { name: "job-runs" }).closest("tr");
    expect(within(done ?? document.body).getByText("Concluído")).toBeInTheDocument();
    expect(within(done ?? document.body).getByText("2 Codificadas")).toBeInTheDocument();
    expect(within(done ?? document.body).getByText(/18\/11\/2026/)).toBeInTheDocument();
    expect(within(done ?? document.body).getByRole("button", { name: "Apagar o trabalho job-done" })).toBeInTheDocument();
    expect(within(running ?? document.body).queryByRole("button", { name: /Apagar/ })).not.toBeInTheDocument();
  });

  it("deletes after the modal confirmation, once per key, and the job leaves the list", async () => {
    const api = withJobs();
    const { user } = renderApp("/jobs");

    await user.click(await screen.findByRole("button", { name: "Apagar o trabalho job-done" }));
    const dialog = screen.getByRole("alertdialog", { name: "Apagar o trabalho job-done?" });
    expect(within(dialog).getByText(/o trabalho é restaurado/)).toBeInTheDocument();
    expect(within(dialog).getByRole("button", { name: "Cancelar" })).toHaveFocus();
    await user.click(within(dialog).getByRole("button", { name: "Sim, apagar" }));

    expect(await screen.findByText("Trabalho apagado.")).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByRole("link", { name: "job-done" })).not.toBeInTheDocument());
    expect(api.keys).toHaveLength(1);
    expect(api.keys[0]).toMatch(/\S+/);
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
  });

  it("cancels with Escape or Cancel, sending nothing, and gives the focus back", async () => {
    const api = withJobs();
    const { user } = renderApp("/jobs");
    const trigger = await screen.findByRole("button", { name: "Apagar o trabalho job-done" });

    await user.click(trigger);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();

    await user.click(trigger);
    await user.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(api.keys).toEqual([]);
  });

  it("shows the server's refusal and keeps the job", async () => {
    withJobs();
    server.use(
      http.delete("/api/jobs/:jobId", () =>
        refused("errors.job.not_deletable", "Só um trabalho terminado pode ser apagado.", 409),
      ),
    );
    const { user } = renderApp("/jobs");

    await user.click(await screen.findByRole("button", { name: "Apagar o trabalho job-done" }));
    await user.click(screen.getByRole("button", { name: "Sim, apagar" }));

    expect(await screen.findByText("Só um trabalho terminado pode ser apagado.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "job-done" })).toBeInTheDocument();
  });

  it("says so when there is no job yet", async () => {
    withJobs([]);
    renderApp("/jobs");

    expect(await screen.findByText("Ainda não há trabalhos.")).toBeInTheDocument();
  });

  it("deletes from the job screen and goes back to the list, out of the recent jobs", async () => {
    withJobs();
    server.use(http.get("/api/jobs/:jobId", () => HttpResponse.json(jobProgress(DONE, "completed", { encoded: 2 }))));
    const { user, router } = renderApp(`/jobs/${DONE}`);
    const sidebar = await screen.findByRole("navigation", { name: "Navegação principal" });
    await within(sidebar).findByRole("link", { name: "job-done" });

    await user.click(await screen.findByRole("button", { name: "Apagar" }));
    await user.click(screen.getByRole("button", { name: "Sim, apagar" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/jobs"));
    expect(within(sidebar).queryByRole("link", { name: "job-done" })).not.toBeInTheDocument();
  });

  it("tells that an upload brought back deleted jobs", async () => {
    withJobs();
    server.use(http.get("/api/jobs/:jobId", () => HttpResponse.json(jobProgress(DONE, "completed", { encoded: 2 }))));
    renderApp(`/jobs/${DONE}?already=%5B%22${DONE}%22%5D&restored=%5B%22${DONE}%22%5D`);

    expect(await screen.findByText(/trouxe de volta trabalhos apagados/)).toBeInTheDocument();
  });

  it("an upload that restores a deleted job puts it back among the recent jobs", async () => {
    withJobs();
    server.use(
      http.post("/api/invoices", () =>
        HttpResponse.json(
          { job_id: "job-newj-0003", status: "queued", invoice_count: 2, existing_job_ids: [DONE], restored_job_ids: [DONE] },
          { status: 202 },
        ),
      ),
      http.get("/api/jobs/:jobId", () => HttpResponse.json(jobProgress(DONE, "completed", { encoded: 1 }))),
    );
    const { user } = renderApp("/");
    await user.upload(await screen.findByLabelText("Ficheiros a carregar"), new File(["%PDF-1.7"], "a.pdf", { type: "application/pdf" }));
    await user.click(screen.getByRole("button", { name: "Carregar 1 ficheiro" }));

    expect(await screen.findByText(/trouxe de volta trabalhos apagados/)).toBeInTheDocument();
    const sidebar = screen.getByRole("navigation", { name: "Navegação principal" });
    expect(within(sidebar).getByRole("link", { name: "job-done" })).toBeInTheDocument();
  });
});

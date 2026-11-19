import { screen, waitFor, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { descriptions } from "@/features/line-review/candidates-table";
import { useLanguage } from "@/shared/i18n/language";
import { jobEntry, jobList, refused, sessionHandlers } from "@/test/api";
import { renderApp } from "@/test/render-app";
import { server } from "@/test/server";

/** The server answers the language it was asked in, as the backend does. */
function withJobsInEitherLanguage() {
  const asked: (string | null)[] = [];
  server.use(...sessionHandlers());
  server.use(
    http.get("/api/jobs", ({ request }) => {
      asked.push(request.headers.get("Accept-Language"));
      return HttpResponse.json(jobList([jobEntry("job-done-0001", "completed", { encoded: 1 })]));
    }),
    http.get("/api/jobs/:jobId", ({ request }) =>
      request.headers.get("Accept-Language") === "pt"
        ? refused("errors.job.not_found", "Trabalho não encontrado.", 404)
        : refused("errors.job.not_found", "Job not found.", 404),
    ),
  );
  return { asked };
}

describe("English and Portuguese (D-3.25)", () => {
  it("starts in English and asks the server for English", async () => {
    useLanguage.setState({ language: "en" });
    const api = withJobsInEitherLanguage();
    renderApp("/jobs");

    expect(await screen.findByRole("heading", { name: "Jobs" })).toBeInTheDocument();
    expect(await screen.findByText("Completed")).toBeInTheDocument();
    expect(api.asked.at(-1)).toBe("en");
    expect(document.documentElement.lang).toBe("en");
  });

  it("switches to Portuguese, texts and server answers alike, and remembers it", async () => {
    useLanguage.setState({ language: "en" });
    const api = withJobsInEitherLanguage();
    const { user } = renderApp("/jobs");
    const switcher = await screen.findByRole("group", { name: "Language" });

    await user.click(within(switcher).getByRole("button", { name: "Português" }));

    expect(await screen.findByRole("heading", { name: "Trabalhos" })).toBeInTheDocument();
    expect(within(screen.getByRole("group", { name: "Idioma" })).getByRole("button", { name: "Português" })).toHaveAttribute("aria-pressed", "true");
    await waitFor(() => expect(api.asked.at(-1)).toBe("pt"));
    expect(document.documentElement.lang).toBe("pt-PT");
    expect(localStorage.getItem("sextante-language")).toContain('"pt"');
  });

  it("shows the server's refusal in the language in force", async () => {
    useLanguage.setState({ language: "en" });
    withJobsInEitherLanguage();
    renderApp("/jobs/job-gone-0009");

    expect(await screen.findByText("This job does not exist.")).toBeInTheDocument();
  });

  it("offers the switch on the sign-in screen too", async () => {
    useLanguage.setState({ language: "en" });
    server.use(http.get("/api/session", () => refused("errors.auth.credential_invalid", "Missing credential.")));
    renderApp("/login");

    expect(await screen.findByRole("heading", { name: "Sign in" })).toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Language" })).toBeInTheDocument();
  });

  it("shows a catalog item in English, or in Portuguese when the catalog has no English name", () => {
    expect(descriptions({ description_pt: "Bilhete Avião", description_en: "Air ticket" }, "en")).toEqual(["Air ticket", "Bilhete Avião"]);
    expect(descriptions({ description_pt: "Sem tradução", description_en: "" }, "en")).toEqual(["Sem tradução", null]);
    expect(descriptions({ description_pt: "Bilhete Avião", description_en: "Air ticket" }, "pt")).toEqual(["Bilhete Avião", "Air ticket"]);
  });
});

import { getRouteApi } from "@tanstack/react-router";

import { shortJobId } from "@/entities/job/job-status";
import { Page } from "@/shared/layout/page";
import { t } from "@/shared/i18n/t";

const route = getRouteApi("/_app/jobs/$jobId/results");

/** The coded lines of one job, filtered and paged from the address. */
export function ResultsPage() {
  const { jobId } = route.useParams();
  return <Page title={t("results.title", { id: shortJobId(jobId) })}>{null}</Page>;
}

import { getRouteApi } from "@tanstack/react-router";

import { Page } from "@/shared/layout/page";
import { t } from "@/shared/i18n/t";

const route = getRouteApi("/_app/jobs/$jobId/results");

export function ResultsPage() {
  const { jobId } = route.useParams();
  return <Page title={`${t("results.title")} · ${jobId.slice(0, 8)}`}>{null}</Page>;
}

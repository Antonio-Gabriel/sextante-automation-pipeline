import { getRouteApi } from "@tanstack/react-router";

import { Page } from "@/shared/layout/page";
import { t } from "@/shared/i18n/t";

const route = getRouteApi("/_app/invoices/$invoiceId/lines/$lineId");

/** The review of one line: candidates, correction and history (frontend ticket 04). */
export function LineReviewPage() {
  route.useParams();
  return <Page title={t("review.title")}>{null}</Page>;
}

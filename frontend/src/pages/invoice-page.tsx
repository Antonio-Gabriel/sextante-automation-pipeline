import { getRouteApi } from "@tanstack/react-router";

import { Page } from "@/shared/layout/page";
import { t } from "@/shared/i18n/t";

const route = getRouteApi("/_app/invoices/$invoiceId");

/** One invoice: extracted header, entity decision and lines (frontend ticket 05). */
export function InvoicePage() {
  route.useParams();
  return <Page title={t("invoice.title")}>{null}</Page>;
}

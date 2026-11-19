import { getRouteApi, Link } from "@tanstack/react-router";
import { Copy } from "lucide-react";
import type { ReactNode } from "react";

import { resolutionLabel } from "@/entities/invoice/entity-resolutions";
import { invoiceStatusView, verdictView } from "@/entities/invoice/invoice-labels";
import { useInvoiceView } from "@/entities/invoice/use-invoice-view";
import { ResolutionForm } from "@/features/entity-resolution/resolution-form";
import { ResultsTable } from "@/features/results/results-table";
import type { components } from "@/shared/api/schema";
import { Page } from "@/shared/layout/page";
import { t } from "@/shared/i18n/t";
import { Badge } from "@/shared/ui-kit/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui-kit/card";

type Invoice = components["schemas"]["InvoiceResponse"];

const route = getRouteApi("/_app/invoices/$invoiceId");
const ENTITY_TITLE_ID = "invoice-entity-title";

function focusEntity() {
  document.getElementById(ENTITY_TITLE_ID)?.focus();
}
const NONE = "common.none" as const;

/** One invoice: extracted header, entity decision, resolution when ambiguous, lines. */
export function InvoicePage() {
  const { invoiceId } = route.useParams();
  const navigate = route.useNavigate();
  const view = useInvoiceView(invoiceId);
  const invoice = view.invoice;
  const filterResults = (jobId: string) =>
    navigate({ to: "/jobs/$jobId/results", params: { jobId }, search: { invoice: invoiceId } });

  return (
    <Page
      title={view.title}
      description={invoice?.supplier_name ?? undefined}
      breadcrumb={
        invoice !== undefined && (
          <Link to="/jobs/$jobId/results" params={{ jobId: invoice.job_id }} className="text-xs text-brand-700 hover:underline">
            {t("invoice.breadcrumb")}
          </Link>
        )
      }
    >
      {view.isPending && <p className="text-sm text-slate-500">{t("invoice.loading")}</p>}
      {view.notFound && <p className="text-sm text-slate-600">{t("invoice.notFound")}</p>}
      {invoice !== undefined && (
        <>
          {invoice.possible_duplicate_of !== null && <DuplicateNotice earlier={invoice.possible_duplicate_of} />}
          <div className="grid gap-6 lg:grid-cols-2">
            <HeaderCard invoice={invoice} />
            <EntityCard invoice={invoice} />
          </div>
          {invoice.resolvable && <ResolutionForm invoiceId={invoiceId} onResolved={focusEntity} />}
          {view.recoding && (
            <p role="status" className="text-sm text-brand-700">
              {t("invoice.recoding")}
            </p>
          )}
          <section className="flex flex-col gap-3">
            <h2 className="text-base font-semibold">{t("invoice.lines")}</h2>
            {view.lines.length === 0 ? (
              <p className="text-sm text-slate-500">{t("invoice.noLines")}</p>
            ) : (
              <ResultsTable lines={view.lines} onFilterInvoice={() => filterResults(invoice.job_id)} />
            )}
            {view.moreLines && (
              <p role="status" className="text-sm text-amber-800">
                {t("invoice.moreLines")}{" "}
                <Link to="/jobs/$jobId/results" params={{ jobId: invoice.job_id }} search={{ invoice: invoiceId }} className="underline">
                  {t("invoice.allLines")}
                </Link>
              </p>
            )}
          </section>
        </>
      )}
    </Page>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <>
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-slate-900">{children}</dd>
    </>
  );
}

function HeaderCard({ invoice }: { invoice: Invoice }) {
  const status = invoiceStatusView(invoice.status);
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("invoice.header")}</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-2 text-sm">
          <Field label={t("invoice.supplier")}>{invoice.supplier_name ?? t(NONE)}</Field>
          <Field label={t("invoice.supplierNif")}>{invoice.supplier_nif ?? t(NONE)}</Field>
          <Field label={t("invoice.number")}>{invoice.invoice_number ?? t(NONE)}</Field>
          <Field label={t("invoice.date")}>{invoice.invoice_date ?? t(NONE)}</Field>
          <Field label={t("invoice.currency")}>{invoice.currency ?? t(NONE)}</Field>
          <Field label={t("invoice.status")}>
            <Badge tone={status.tone}>{t(status.label)}</Badge>
          </Field>
          {invoice.status_reason !== null && <Field label={t("invoice.statusReason")}>{invoice.status_reason.message}</Field>}
        </dl>
      </CardContent>
    </Card>
  );
}

function EntityCard({ invoice }: { invoice: Invoice }) {
  const verdict = verdictView(invoice.entity_verdict);
  const resolution = invoice.entity_resolution;
  return (
    <Card>
      <CardHeader>
        <CardTitle id={ENTITY_TITLE_ID} tabIndex={-1} className="outline-none">
          {t("invoice.entity")}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-2 text-sm">
          <Field label={t("invoice.billedEntity")}>{invoice.billed_entity_detected ?? t(NONE)}</Field>
          <Field label={t("invoice.verdictLabel")}>
            {verdict === null ? t(NONE) : <Badge tone={verdict.tone}>{t(verdict.label)}</Badge>}
          </Field>
          {invoice.entity_reason !== null && <Field label={t("invoice.ambiguityReason")}>{invoice.entity_reason.message}</Field>}
          <Field label={t("invoice.sheet")}>{invoice.target_sheet ?? t(NONE)}</Field>
          {resolution !== null && (
            <Field label={t("invoice.resolution.title")}>
              <p>{t("invoice.resolution.recorded", { verdict: t(resolutionLabel(resolution.verdict) ?? NONE) })}</p>
              <p className="text-slate-600">{resolution.note}</p>
            </Field>
          )}
        </dl>
      </CardContent>
    </Card>
  );
}

function DuplicateNotice({ earlier }: { earlier: NonNullable<Invoice["possible_duplicate_of"]> }) {
  return (
    <div role="status" className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
      <Copy className="size-5 shrink-0" aria-hidden />
      <p className="flex-1">{t("invoice.duplicate", { number: earlier.invoice_number ?? t(NONE) })}</p>
      <Link to="/invoices/$invoiceId" params={{ invoiceId: earlier.invoice_id }} className="font-medium text-amber-900 underline">
        {t("invoice.duplicateOpen")}
      </Link>
    </div>
  );
}

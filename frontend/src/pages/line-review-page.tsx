import { getRouteApi, Link } from "@tanstack/react-router";
import { TriangleAlert } from "lucide-react";

import { confidenceView, reviewView } from "@/entities/result/result-labels";
import { CandidatesTable } from "@/features/line-review/candidates-table";
import { CodingHistory } from "@/features/line-review/coding-history";
import { ReviewActions } from "@/features/line-review/review-actions";
import { useLineReview } from "@/features/line-review/use-line-review";
import { useReviewActions } from "@/features/line-review/use-review-actions";
import type { components } from "@/shared/api/schema";
import { Page } from "@/shared/layout/page";
import { t } from "@/shared/i18n/t";
import { Badge } from "@/shared/ui-kit/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui-kit/card";

type ResultLine = components["schemas"]["ResultLineResponse"];

const route = getRouteApi("/_app/invoices/$invoiceId/lines/$lineId");
const NONE = "common.none" as const;

/** The review of one line: coding in force, every item of its sheet, decision, history. */
export function LineReviewPage() {
  const { invoiceId, lineId } = route.useParams();
  const review = useLineReview(invoiceId, lineId);
  const { line, invoice } = review;

  return (
    <Page
      title={t("review.title", { position: line?.line_position ?? "" })}
      description={line?.line_description}
      breadcrumb={
        invoice !== undefined && (
          <Link to="/invoices/$invoiceId" params={{ invoiceId }} className="text-xs text-brand-700 hover:underline">
            {t("review.breadcrumb", { number: invoice.invoice_number ?? t(NONE) })}
          </Link>
        )
      }
    >
      {review.isPending && <p className="text-sm text-slate-500">{t("review.loading")}</p>}
      {(review.notFound || (!review.isPending && line === undefined)) && (
        <p className="text-sm text-slate-600">{t("review.notFound")}</p>
      )}
      {line !== undefined && (
        <>
          <CurrentCoding line={line} />
          {review.targetSheet === null || line.encoded_line_id === null ? (
            <NoSheet invoiceId={invoiceId} />
          ) : (
            <Decision line={line} encodedLineId={line.encoded_line_id} sheet={review.targetSheet} candidates={review.candidates} />
          )}
          <CodingHistory codings={review.history} />
        </>
      )}
    </Page>
  );
}

interface DecisionProps {
  line: ResultLine;
  encodedLineId: string;
  sheet: string;
  candidates: components["schemas"]["CandidateResponse"][];
}

function Decision({ line, encodedLineId, sheet, candidates }: DecisionProps) {
  const actions = useReviewActions(encodedLineId);
  return (
    <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold">{t("review.candidates.title", { sheet })}</h2>
        <p className="text-sm text-slate-500">{t("review.candidates.description")}</p>
        <CandidatesTable
          candidates={candidates}
          currentItem={line.item_number}
          choice={actions.form.register("item_number")}
          disabled={actions.isPending}
        />
      </section>
      <ReviewActions actions={actions} pending={line.review_status === "pending"} />
    </div>
  );
}

function CurrentCoding({ line }: { line: ResultLine }) {
  const confidence = confidenceView(line.confidence);
  const status = reviewView(line.review_status);
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("review.current")}</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-2 text-sm">
          <dt className="text-slate-500">{t("review.item")}</dt>
          <dd className="font-mono">
            {line.item_number ?? t(NONE)} <span className="font-sans text-slate-600">{line.catalog_description}</span>
          </dd>
          <dt className="text-slate-500">{t("review.confidence")}</dt>
          <dd>{confidence === null ? t(NONE) : <Badge tone={confidence.tone}>{t(confidence.label)}</Badge>}</dd>
          <dt className="text-slate-500">{t("review.status")}</dt>
          <dd><Badge tone={status.tone}>{t(status.label)}</Badge></dd>
          <dt className="text-slate-500">{t("review.flags")}</dt>
          <dd>
            <ul>
              {[...line.flags, ...line.notes].map((item, index) => (
                <li key={`${index}-${item.code}`}>{item.message}</li>
              ))}
            </ul>
          </dd>
          <dt className="text-slate-500">{t("review.reviewNote")}</dt>
          <dd>{line.review_note ?? t(NONE)}</dd>
        </dl>
      </CardContent>
    </Card>
  );
}

function NoSheet({ invoiceId }: { invoiceId: string }) {
  return (
    <div role="status" className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
      <TriangleAlert className="size-5 shrink-0" aria-hidden />
      <p className="flex-1">{t("review.noSheet")}</p>
      <Link to="/invoices/$invoiceId" params={{ invoiceId }} className="font-medium underline">
        {t("review.openInvoice")}
      </Link>
    </div>
  );
}

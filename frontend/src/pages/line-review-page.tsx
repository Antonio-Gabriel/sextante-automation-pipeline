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
import { t, type MessageKey } from "@/shared/i18n/t";
import { Badge } from "@/shared/ui-kit/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui-kit/card";

type ResultLine = components["schemas"]["ResultLineResponse"];
type Candidate = components["schemas"]["CandidateResponse"];

const route = getRouteApi("/_app/invoices/$invoiceId/lines/$lineId");
const NONE = "common.none" as const;

/**
 * The review of one line: coding in force, every item of its sheet, decision, history.
 *
 * Example:
 *   route "/invoices/$invoiceId/lines/$lineId" -> <LineReviewPage />
 */
export function LineReviewPage() {
  const { invoiceId, lineId } = route.useParams();
  const review = useLineReview(invoiceId, lineId);
  const { line, invoice } = review;

  return (
    <Page
      title={t("review.title", { position: line?.line_position ?? "" })}
      description={line?.line_description}
      breadcrumb={invoice !== undefined && <InvoiceLink invoiceId={invoiceId} label={t("review.breadcrumb", { number: invoice.invoice_number ?? t(NONE) })} />}
    >
      {review.stateText !== null && <p className="text-sm text-slate-600">{t(review.stateText)}</p>}
      {review.failure !== null && (
        <p role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{review.failure}</p>
      )}
      {review.state === "ready" && line !== undefined && (
        <>
          <CurrentCoding line={line} />
          {review.decision === "ready" && line.encoded_line_id !== null && review.targetSheet !== null ? (
            <Decision encodedLineId={line.encoded_line_id} currentItem={line.item_number} reviewPending={review.reviewPending} sheet={review.targetSheet} candidates={review.candidates} />
          ) : (
            <Blocked text={review.decision === "noSheet" ? "review.noSheet" : "review.notCoded"} invoiceId={invoiceId} />
          )}
          <CodingHistory codings={review.history} />
        </>
      )}
    </Page>
  );
}

function InvoiceLink({ invoiceId, label }: { invoiceId: string; label: string }) {
  return (
    <Link to="/invoices/$invoiceId" params={{ invoiceId }} className="text-xs text-brand-700 hover:underline">
      {label}
    </Link>
  );
}

interface DecisionProps {
  encodedLineId: string;
  currentItem: string | null;
  reviewPending: boolean;
  sheet: string;
  candidates: Candidate[];
}

function Decision({ encodedLineId, currentItem, reviewPending, sheet, candidates }: DecisionProps) {
  const actions = useReviewActions(encodedLineId);
  return (
    <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
      <section className="flex flex-col gap-2">
        <h2 className="text-base font-semibold">{t("review.candidates.title", { sheet })}</h2>
        <p className="text-sm text-slate-500">{t("review.candidates.description")}</p>
        <CandidatesTable candidates={candidates} currentItem={currentItem} choice={actions.register("item_number")} disabled={actions.isPending} />
      </section>
      <ReviewActions
        registerNote={actions.register("note")}
        noteError={actions.noteError}
        remaining={actions.remaining}
        reviewPending={reviewPending}
        isPending={actions.isPending}
        canCorrect={actions.canCorrect}
        correctLabel={actions.correctLabel}
        failure={actions.failure}
        onAccept={() => void actions.accept()}
        onCorrect={() => void actions.correct()}
      />
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

function Blocked({ text, invoiceId }: { text: MessageKey; invoiceId: string }) {
  return (
    <div role="status" className="flex items-center gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
      <TriangleAlert className="size-5 shrink-0" aria-hidden />
      <p className="flex-1">{t(text)}</p>
      <Link to="/invoices/$invoiceId" params={{ invoiceId }} className="font-medium underline">
        {t("review.openInvoice")}
      </Link>
    </div>
  );
}

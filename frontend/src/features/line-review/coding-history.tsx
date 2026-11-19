import { confidenceView, reviewView } from "@/entities/result/result-labels";
import type { components } from "@/shared/api/schema";
import { shortDigest } from "@/shared/format";
import { t } from "@/shared/i18n/t";
import { Badge } from "@/shared/ui-kit/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui-kit/card";

type Coding = components["schemas"]["CodingHistoryResponse"];

const NONE = "common.none" as const;

/**
 * Every coding of the line, newest first, in force or superseded, with its review.
 *
 * Example:
 *   <CodingHistory codings={history} />
 */
export function CodingHistory({ codings }: { codings: readonly Coding[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("review.history.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        {codings.length === 0 ? (
          <p className="text-sm text-slate-500">{t("review.history.empty")}</p>
        ) : (
          <ol className="flex flex-col gap-3">
            {codings.map((coding) => (
              <CodingEntry key={coding.encoded_line_id} coding={coding} />
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}

function CodingEntry({ coding }: { coding: Coding }) {
  const confidence = confidenceView(coding.confidence);
  const review = coding.review === null ? null : reviewView(coding.review.review_status);
  return (
    <li className="rounded-lg border border-slate-200 p-3 text-sm">
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <Badge tone={coding.in_force ? "success" : "neutral"}>
          {t(coding.in_force ? "review.history.inForce" : "review.history.superseded")}
        </Badge>
        <span className="text-xs text-slate-500">{t("review.history.encodedAt", { date: coding.encoded_at })}</span>
        {coding.superseded_at !== null && (
          <span className="text-xs text-slate-500">{t("review.history.supersededAt", { date: coding.superseded_at })}</span>
        )}
      </div>
      <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-1">
        <dt className="text-slate-500">{t("review.history.item")}</dt>
        <dd className="font-mono">{coding.item_number ?? t(NONE)}</dd>
        <dt className="text-slate-500">{t("review.history.confidence")}</dt>
        <dd>{confidence === null ? t(NONE) : <Badge tone={confidence.tone}>{t(confidence.label)}</Badge>}</dd>
        <dt className="text-slate-500">{t("review.history.prompt")}</dt>
        <dd>{coding.prompt_version ?? t(NONE)}</dd>
        <dt className="text-slate-500">{t("review.history.model")}</dt>
        <dd>{coding.model_id ?? t(NONE)}</dd>
        <dt className="text-slate-500">{t("review.history.catalog")}</dt>
        <dd className="font-mono" title={coding.catalog_digest}>{shortDigest(coding.catalog_digest)}</dd>
        <dt className="text-slate-500">{t("review.history.review")}</dt>
        <dd>
          {review === null ? t("review.history.noReview") : <Badge tone={review.tone}>{t(review.label)}</Badge>}
          {coding.review?.note != null && <p className="mt-1 text-slate-600">{coding.review.note}</p>}
        </dd>
      </dl>
    </li>
  );
}

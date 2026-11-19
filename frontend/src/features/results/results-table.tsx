import { Link } from "@tanstack/react-router";
import { Filter } from "lucide-react";

import { confidenceView, reviewView, yesNo } from "@/entities/result/result-labels";
import type { components } from "@/shared/api/schema";
import { t, type MessageKey } from "@/shared/i18n/t";
import { Badge } from "@/shared/ui-kit/badge";

import { useFilterNavigation } from "./use-filter-navigation";

type ResultLine = components["schemas"]["ResultLineResponse"];

const COLUMNS: readonly MessageKey[] = [
  "results.columns.invoice",
  "results.columns.entity",
  "results.columns.exactMatch",
  "results.columns.sheet",
  "results.columns.description",
  "results.columns.item",
  "results.columns.catalogDescription",
  "results.columns.confidence",
  "results.columns.review",
  "results.columns.flags",
  "results.columns.reviewNote",
];

const CELL = "px-3 py-2.5 align-top";

/**
 * The coded lines, one per row. Invoice content is always text, never markup.
 *
 * Example:
 *   <ResultsTable jobId={jobId} lines={lines} />
 */
export function ResultsTable({ jobId, lines }: { jobId: string; lines: readonly ResultLine[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="w-full min-w-[1200px] text-left text-sm">
        <thead className="border-b border-slate-200 bg-slate-50 text-xs font-medium uppercase tracking-wide text-slate-500">
          <tr>
            {COLUMNS.map((column) => (
              <th key={column} scope="col" className="px-3 py-2.5 font-medium">
                {t(column)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {lines.map((line) => (
            <ResultRow key={line.invoice_line_id} jobId={jobId} line={line} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ResultRow({ jobId, line }: { jobId: string; line: ResultLine }) {
  const { setFilter } = useFilterNavigation(jobId);
  const confidence = confidenceView(line.confidence);
  const review = reviewView(line.review_status);
  const lineParams = { invoiceId: line.invoice_id, lineId: line.invoice_line_id };
  return (
    <tr className="hover:bg-slate-50">
      <td className={CELL}>
        <div className="flex items-center gap-1">
          <Link to="/invoices/$invoiceId" params={{ invoiceId: line.invoice_id }} className="font-medium text-brand-700 hover:underline">
            {line.invoice_number ?? t("results.noValue")}
          </Link>
          <button
            type="button"
            aria-label={t("results.filters.filterByInvoice")}
            title={t("results.filters.filterByInvoice")}
            onClick={() => setFilter({ invoice: line.invoice_id })}
            className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          >
            <Filter className="size-3.5" />
          </button>
        </div>
      </td>
      <td className={CELL}>{line.billed_entity_detected ?? t("results.noValue")}</td>
      <td className={CELL}>{t(yesNo(line.exact_entity_match))}</td>
      <td className={CELL}>{line.target_sheet ?? t("results.noValue")}</td>
      <td className={`${CELL} max-w-xs`}>
        <Link to="/invoices/$invoiceId/lines/$lineId" params={lineParams} className="text-slate-900 hover:text-brand-700 hover:underline" title={t("results.openLine")}>
          {line.line_description}
        </Link>
      </td>
      <td className={`${CELL} font-mono`}>{line.item_number ?? t("results.noValue")}</td>
      <td className={`${CELL} max-w-xs text-slate-600`}>{line.catalog_description ?? t("results.noValue")}</td>
      <td className={CELL}>
        {confidence === null ? t("results.noValue") : <Badge tone={confidence.tone}>{t(confidence.label)}</Badge>}
      </td>
      <td className={CELL}>
        <Badge tone={review.tone}>{t(review.label)}</Badge>
      </td>
      <td className={`${CELL} max-w-xs`}>
        <ul className="flex flex-col gap-1">
          {[...line.flags, ...line.notes].map((item) => (
            <li key={item.code} className="text-xs text-slate-700">
              {item.message}
            </li>
          ))}
        </ul>
      </td>
      <td className={`${CELL} max-w-xs text-slate-600`}>{line.review_note ?? t("results.noValue")}</td>
    </tr>
  );
}

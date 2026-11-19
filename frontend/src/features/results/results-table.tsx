import { Link } from "@tanstack/react-router";
import { ChevronRight, Filter } from "lucide-react";

import { confidenceView, reviewView, yesNo } from "@/entities/result/result-labels";
import type { components } from "@/shared/api/schema";
import { t, type MessageKey } from "@/shared/i18n/t";
import { Badge } from "@/shared/ui-kit/badge";
import { cn } from "@/shared/ui-kit/cn";

import { LINE_ROUTE, useRowOpensLine } from "./use-row-opens-line";


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
// The last column stays in view when the table scrolls sideways: the way into the line.
const ACTION_CELL = "sticky right-0 bg-white px-3 py-2 align-top shadow-[-8px_0_8px_-8px_rgba(15,23,42,0.12)] group-hover:bg-slate-50";

interface ResultsTableProps {
  lines: readonly ResultLine[];
  onFilterInvoice: (invoiceId: string) => void;
}

/**
 * The coded lines, one per row; a click anywhere on a row opens its review, and the
 * description and the last column are its links. Invoice content is always text, never markup.
 *
 * Example:
 *   <ResultsTable lines={lines} onFilterInvoice={navigation.chooseInvoice} />
 */
export function ResultsTable({ lines, onFilterInvoice }: ResultsTableProps) {
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
            <th scope="col" className="sticky right-0 bg-slate-50 px-3 py-2.5 font-medium">
              <span className="sr-only">{t("results.columns.action")}</span>
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {lines.map((line) => (
            <ResultRow key={line.invoice_line_id} line={line} onFilterInvoice={onFilterInvoice} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface ResultRowProps {
  line: ResultLine;
  onFilterInvoice: (invoiceId: string) => void;
}

function ResultRow({ line, onFilterInvoice }: ResultRowProps) {
  const invoice = line.invoice_number ?? t("common.none");
  const filterLabel = t("results.filters.filterByInvoice", { invoice });
  const confidence = confidenceView(line.confidence);
  const review = reviewView(line.review_status);
  const lineParams = { invoiceId: line.invoice_id, lineId: line.invoice_line_id };
  const openFromRow = useRowOpensLine(lineParams);
  const pending = line.review_status === "pending";
  const actionLabel = t(pending ? "results.reviewLine" : "results.openLineN", { position: line.line_position });
  return (
    <tr className="group cursor-pointer hover:bg-slate-50" onClick={openFromRow}>
      <td className={CELL}>
        <div className="flex items-center gap-1">
          <Link to="/invoices/$invoiceId" params={{ invoiceId: line.invoice_id }} className="font-medium text-brand-700 hover:underline">
            {invoice}
          </Link>
          <button
            type="button"
            aria-label={filterLabel}
            title={filterLabel}
            onClick={() => onFilterInvoice(line.invoice_id)}
            className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          >
            <Filter className="size-3.5" />
          </button>
        </div>
      </td>
      <td className={CELL}>{line.billed_entity_detected ?? t("common.none")}</td>
      <td className={CELL}>{t(yesNo(line.exact_entity_match))}</td>
      <td className={CELL}>{line.target_sheet ?? t("common.none")}</td>
      <td className={`${CELL} max-w-xs`}>
        <Link
          to={LINE_ROUTE}
          params={lineParams}
          className="font-medium text-brand-700 underline decoration-brand-200 decoration-1 underline-offset-[3px] hover:decoration-brand-700"
          title={t("results.openLine")}
        >
          {line.line_description.trim() === "" ? t("results.openLine") : line.line_description}
        </Link>
      </td>
      <td className={`${CELL} font-mono`}>{line.item_number ?? t("common.none")}</td>
      <td className={`${CELL} max-w-xs text-slate-600`}>{line.catalog_description ?? t("common.none")}</td>
      <td className={CELL}>
        {confidence === null ? t("common.none") : <Badge tone={confidence.tone}>{t(confidence.label)}</Badge>}
      </td>
      <td className={CELL}>
        <Badge tone={review.tone}>{t(review.label)}</Badge>
      </td>
      <td className={`${CELL} max-w-xs`}>
        <ul className="flex flex-col gap-1">
          {[...line.flags, ...line.notes].map((item, index) => (
            <li key={`${index}-${item.code}`} className="text-xs text-slate-700">
              {item.message}
            </li>
          ))}
        </ul>
      </td>
      <td className={`${CELL} max-w-xs text-slate-600`}>{line.review_note ?? t("common.none")}</td>
      <td className={ACTION_CELL}>
        <Link
          to={LINE_ROUTE}
          params={lineParams}
          aria-label={actionLabel}
          className={cn(
            "inline-flex h-8 items-center gap-1 rounded-lg px-2.5 text-xs font-medium whitespace-nowrap transition-colors [&_svg]:size-3.5",
            pending
              ? "bg-brand-700 text-white shadow-sm hover:bg-brand-800"
              : "border border-slate-200 bg-white text-slate-700 hover:border-brand-300 hover:text-brand-700",
          )}
        >
          {t(pending ? "results.review" : "results.open")}
          <ChevronRight aria-hidden />
        </Link>
      </td>
    </tr>
  );
}

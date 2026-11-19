import type { UseFormRegisterReturn } from "react-hook-form";

import type { components } from "@/shared/api/schema";
import { formatNumber } from "@/shared/format";
import { t } from "@/shared/i18n/t";
import { Badge } from "@/shared/ui-kit/badge";

type Candidate = components["schemas"]["CandidateResponse"];

const SCORE_DIGITS = 3;
const CELL = "px-3 py-2 align-top";

interface CandidatesTableProps {
  candidates: readonly Candidate[];
  currentItem: string | null;
  /** The radio of each row registers the item chosen for the correction. */
  choice: UseFormRegisterReturn<"item_number">;
  disabled: boolean;
}

/**
 * Every item of the line's target sheet, best score first, the model's choice marked.
 * Only these items can be chosen: the selector offers the target sheet alone (§7).
 *
 * Example:
 *   <CandidatesTable candidates={candidates} currentItem="O00004" choice={register("item_number")} disabled={false} />
 */
export function CandidatesTable({ candidates, currentItem, choice, disabled }: CandidatesTableProps) {
  return (
    <fieldset className="max-h-[28rem] overflow-auto rounded-xl border border-slate-200 bg-white">
      <legend className="sr-only">{t("review.candidates.legend")}</legend>
      <table className="w-full text-left text-sm">
        <thead className="sticky top-0 border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th scope="col" className="w-10 px-3 py-2">
              <span className="sr-only">{t("review.candidates.chooseColumn")}</span>
            </th>
            <th scope="col" className="px-3 py-2 font-medium">{t("review.candidates.rank")}</th>
            <th scope="col" className="px-3 py-2 font-medium">{t("review.candidates.item")}</th>
            <th scope="col" className="px-3 py-2 font-medium">{t("review.candidates.catalogDescription")}</th>
            <th scope="col" className="px-3 py-2 text-right font-medium">{t("review.candidates.score")}</th>
            <th scope="col" className="px-3 py-2 font-medium">{t("review.candidates.model")}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {candidates.map((candidate) => (
            <tr key={candidate.item_number} className="has-[:checked]:bg-brand-50">
              <td className={CELL}>
                <input
                  type="radio"
                  value={candidate.item_number}
                  disabled={disabled}
                  aria-label={t("review.candidates.choose", { item: candidate.item_number })}
                  className="accent-brand-700"
                  {...choice}
                />
              </td>
              <td className={`${CELL} tabular-nums text-slate-500`}>{candidate.rank}</td>
              <td className={`${CELL} font-mono`}>
                {candidate.item_number}
                {candidate.item_number === currentItem && (
                  <Badge tone="neutral" className="ml-2">{t("review.candidates.current")}</Badge>
                )}
              </td>
              <td className={CELL}>
                <p>{candidate.description_pt}</p>
                <p className="text-xs text-slate-500">{candidate.description_en}</p>
              </td>
              <td className={`${CELL} text-right tabular-nums`}>{formatNumber(candidate.score, SCORE_DIGITS)}</td>
              <td className={CELL}>
                {candidate.chosen_by_model && <Badge tone="brand">{t("review.candidates.chosenByModel")}</Badge>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </fieldset>
  );
}

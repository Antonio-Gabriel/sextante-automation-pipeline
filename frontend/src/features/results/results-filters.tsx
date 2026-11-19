import { FilterX, X } from "lucide-react";

import { CONFIDENCES, TARGET_SHEETS, type ResultFilters } from "@/entities/result/result-filters";
import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";
import { Label } from "@/shared/ui-kit/label";
import { Select } from "@/shared/ui-kit/select";

import { useFilterNavigation } from "./use-filter-navigation";

const ANY = "";
const FLAGGED = { flagged: "true", unflagged: "false" } as const;

interface ResultsFiltersProps {
  jobId: string;
  filters: ResultFilters;
}

/**
 * Confidence, sheet and flag filters, and the invoice filter when one is set.
 *
 * Example:
 *   <ResultsFilters jobId={jobId} filters={filters} />
 */
export function ResultsFilters({ jobId, filters }: ResultsFiltersProps) {
  const { setFilter, clear } = useFilterNavigation(jobId);
  const flagged = filters.flagged === undefined ? ANY : String(filters.flagged);

  return (
    <section aria-label={t("results.filters.label")} className="flex flex-wrap items-end gap-3">
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="filter-confidence">{t("results.filters.confidence")}</Label>
        <Select
          id="filter-confidence"
          value={filters.confidence ?? ANY}
          onChange={(event) =>
            setFilter({ confidence: CONFIDENCES.find((c) => c === event.target.value) })
          }
        >
          <option value={ANY}>{t("results.filters.any")}</option>
          {CONFIDENCES.map((confidence) => (
            <option key={confidence} value={confidence}>
              {t(`values.confidence.${confidence}`)}
            </option>
          ))}
        </Select>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="filter-sheet">{t("results.filters.sheet")}</Label>
        <Select
          id="filter-sheet"
          value={filters.sheet ?? ANY}
          onChange={(event) => setFilter({ sheet: TARGET_SHEETS.find((s) => s === event.target.value) })}
        >
          <option value={ANY}>{t("results.filters.any")}</option>
          {TARGET_SHEETS.map((sheet) => (
            <option key={sheet} value={sheet}>
              {sheet}
            </option>
          ))}
        </Select>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor="filter-flagged">{t("results.filters.flagged")}</Label>
        <Select
          id="filter-flagged"
          value={flagged}
          onChange={(event) =>
            setFilter({ flagged: event.target.value === ANY ? undefined : event.target.value === FLAGGED.flagged })
          }
        >
          <option value={ANY}>{t("results.filters.any")}</option>
          <option value={FLAGGED.flagged}>{t("results.filters.flaggedOnly")}</option>
          <option value={FLAGGED.unflagged}>{t("results.filters.unflaggedOnly")}</option>
        </Select>
      </div>
      {filters.invoice !== undefined && (
        <Button variant="outline" onClick={() => setFilter({ invoice: undefined })}>
          <X />
          {t("results.filters.clearInvoice")}
        </Button>
      )}
      <Button variant="ghost" onClick={clear}>
        <FilterX />
        {t("results.filters.clear")}
      </Button>
    </section>
  );
}

import { FilterX, X } from "lucide-react";
import type { ReactNode } from "react";

import { CONFIDENCES, TARGET_SHEETS, type ResultFilters } from "@/entities/result/result-filters";
import { confidenceView } from "@/entities/result/result-labels";
import { t, type MessageKey } from "@/shared/i18n/t";
import { Badge } from "@/shared/ui-kit/badge";
import { Button } from "@/shared/ui-kit/button";
import { Label } from "@/shared/ui-kit/label";
import { Select } from "@/shared/ui-kit/select";

import { useFilterNavigation } from "./use-filter-navigation";

const ANY = "";

interface ResultsFiltersProps {
  jobId: string;
  filters: ResultFilters;
  /** The filtered invoice's number, when known; its id otherwise. */
  invoiceLabel: string | null;
}

/**
 * Confidence, sheet and flag filters, and the invoice filter when one is set.
 *
 * Example:
 *   <ResultsFilters jobId={jobId} filters={filters} invoiceLabel="FT 2026/17" />
 */
export function ResultsFilters({ jobId, filters, invoiceLabel }: ResultsFiltersProps) {
  const navigation = useFilterNavigation(jobId);
  const flagged = filters.flagged === undefined ? ANY : String(filters.flagged);

  return (
    <section aria-label={t("results.filters.label")} className="flex flex-wrap items-end gap-3">
      <FilterSelect id="filter-confidence" label="results.filters.confidence" value={filters.confidence ?? ANY} onChange={navigation.chooseConfidence}>
        {CONFIDENCES.map((confidence) => (
          <option key={confidence} value={confidence}>
            {t(confidenceView(confidence)?.label ?? "results.filters.any")}
          </option>
        ))}
      </FilterSelect>
      <FilterSelect id="filter-sheet" label="results.filters.sheet" value={filters.sheet ?? ANY} onChange={navigation.chooseSheet}>
        {TARGET_SHEETS.map((sheet) => (
          <option key={sheet} value={sheet}>
            {sheet}
          </option>
        ))}
      </FilterSelect>
      <FilterSelect id="filter-flagged" label="results.filters.flagged" value={flagged} onChange={navigation.chooseFlagged}>
        <option value="true">{t("results.filters.flaggedOnly")}</option>
        <option value="false">{t("results.filters.unflaggedOnly")}</option>
      </FilterSelect>
      {filters.invoice !== undefined && (
        <div className="flex items-center gap-2">
          <Badge tone="brand">{t("results.filters.invoiceActive", { invoice: invoiceLabel ?? filters.invoice })}</Badge>
          <Button variant="outline" size="sm" onClick={() => navigation.chooseInvoice(undefined)}>
            <X />
            {t("results.filters.clearInvoice")}
          </Button>
        </div>
      )}
      <Button variant="ghost" onClick={navigation.clear}>
        <FilterX />
        {t("results.filters.clear")}
      </Button>
    </section>
  );
}

interface FilterSelectProps {
  id: string;
  label: MessageKey;
  value: string;
  onChange: (value: string) => void;
  children: ReactNode;
}

function FilterSelect({ id, label, value, onChange, children }: FilterSelectProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{t(label)}</Label>
      <Select id={id} value={value} onChange={(event) => onChange(event.target.value)}>
        <option value={ANY}>{t("results.filters.any")}</option>
        {children}
      </Select>
    </div>
  );
}

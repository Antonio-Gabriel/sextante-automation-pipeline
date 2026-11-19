import { formatNumber } from "@/shared/format";
import { t } from "@/shared/i18n/t";

const UNITS = ["B", "KB", "MB", "GB"] as const;
const STEP = 1024;

/**
 * A file size with its unit from the catalog.
 *
 * Example:
 *   formatBytes(1536) // "1,5 KB"
 */
export function formatBytes(bytes: number): string {
  let value = bytes;
  let unit = 0;
  while (value >= STEP && unit < UNITS.length - 1) {
    value /= STEP;
    unit += 1;
  }
  const name = UNITS[unit] ?? "B";
  return t("units.size", { value: formatNumber(value, unit === 0 ? 0 : 1), unit: t(`units.${name}`) });
}

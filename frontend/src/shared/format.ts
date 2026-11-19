const LOCALE = "pt-PT";

/**
 * A number in the Portuguese format.
 *
 * Example:
 *   formatNumber(12500) // "12 500"
 */
export function formatNumber(value: number, fractionDigits = 0): string {
  return value.toLocaleString(LOCALE, { maximumFractionDigits: fractionDigits });
}

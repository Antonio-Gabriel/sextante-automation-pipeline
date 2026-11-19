const LOCALE = "pt-PT";
const DIGEST_SHOWN = 12;

/**
 * A number in the Portuguese format.
 *
 * Example:
 *   formatNumber(12500) // "12 500"
 */
export function formatNumber(value: number, fractionDigits = 0): string {
  return value.toLocaleString(LOCALE, { maximumFractionDigits: fractionDigits });
}

/**
 * A moment of the server (ISO 8601) as a short Portuguese date and time, in local time.
 *
 * Example:
 *   formatDateTime("2026-11-18T09:00:00+00:00") // "18/11/2026, 09:00"
 */
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(LOCALE, {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * The first characters of a SHA-256 digest, enough to tell versions apart on screen.
 *
 * Example:
 *   shortDigest("739ca559901d5731...") // "739ca559901d"
 */
export function shortDigest(digest: string): string {
  return digest.slice(0, DIGEST_SHOWN);
}

/**
 * A number the OpenAPI document must carry; a missing one is a broken contract, never 0.
 *
 * Example:
 *   requireNumber(schema.maxLength, "CorrectionRequest.note.maxLength") // 500
 */
export function requireNumber(value: number | undefined, name: string): number {
  if (value === undefined) throw new Error(`OpenAPI contract lacks ${name}. Expected a number.`);
  return value;
}

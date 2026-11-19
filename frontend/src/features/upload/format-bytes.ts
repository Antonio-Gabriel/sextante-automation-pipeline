const UNITS = ["B", "KB", "MB", "GB"] as const;
const STEP = 1024;

/** 1536 → "1,5 KB", in the Portuguese number format. */
export function formatBytes(bytes: number): string {
  let value = bytes;
  let unit = 0;
  while (value >= STEP && unit < UNITS.length - 1) {
    value /= STEP;
    unit += 1;
  }
  const digits = unit === 0 ? 0 : 1;
  return `${value.toLocaleString("pt-PT", { maximumFractionDigits: digits })} ${UNITS[unit] ?? ""}`;
}

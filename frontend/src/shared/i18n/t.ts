import { pt } from "./pt";

// "login.title", "home.logout", ...: every leaf of the catalog, checked at compile time.
type Leaves<T> = {
  [K in keyof T & string]: T[K] extends string ? K : `${K}.${Leaves<T[K]>}`;
}[keyof T & string];

export type MessageKey = Leaves<typeof pt>;

/** The Portuguese text of a catalog key, with {name} placeholders filled from values. */
export function t(key: MessageKey, values: Record<string, string | number> = {}): string {
  let node: unknown = pt;
  for (const part of key.split(".")) {
    node = typeof node === "object" && node !== null ? Reflect.get(node, part) : undefined;
  }
  // Unreachable for a MessageKey; kept so a broken catalog shows the key, not a crash.
  const text = typeof node === "string" ? node : key;
  return text.replace(/\{(\w+)\}/g, (match, name: string) =>
    name in values ? String(values[name]) : match,
  );
}

/**
 * The text for one or for many, the count filled in {count}.
 *
 * Example:
 *   tCount(1, "upload.submitOne", "upload.submit") // "Carregar 1 ficheiro"
 */
export function tCount(
  count: number,
  one: MessageKey,
  many: MessageKey,
  values: Record<string, string | number> = {},
): string {
  return t(count === 1 ? one : many, { ...values, count });
}

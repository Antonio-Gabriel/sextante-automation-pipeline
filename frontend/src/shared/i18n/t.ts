import { pt } from "./pt";

// "login.title", "home.logout", ...: every leaf of the catalog, checked at compile time.
type Leaves<T> = {
  [K in keyof T & string]: T[K] extends string ? K : `${K}.${Leaves<T[K]>}`;
}[keyof T & string];

export type MessageKey = Leaves<typeof pt>;

/** The Portuguese text of a catalog key. */
export function t(key: MessageKey): string {
  let node: unknown = pt;
  for (const part of key.split(".")) {
    node = typeof node === "object" && node !== null ? Reflect.get(node, part) : undefined;
  }
  // Unreachable for a MessageKey; kept so a broken catalog shows the key, not a crash.
  return typeof node === "string" ? node : key;
}

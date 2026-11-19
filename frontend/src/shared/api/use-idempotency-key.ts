import { useRef } from "react";

/**
 * Idempotency-Keys for one kind of action (SEC-19). A key is made before the first send
 * of a body and kept while the body is the same, so a double click or a retry after a
 * lost answer acts once. A different body gets a new key: the server refuses a key
 * reused with another body. After the action succeeds, renew for the next one.
 *
 * Example:
 *   const keys = useIdempotencyKey();
 *   const key = keys.keyFor(body);
 *   mutate({ params: { header: { "Idempotency-Key": key } }, body }, { onSuccess: keys.renew });
 */
export function useIdempotencyKey() {
  const last = useRef<{ key: string; body: string } | null>(null);
  return {
    keyFor: (body: unknown): string => {
      const fingerprint = JSON.stringify(body ?? null);
      if (last.current === null || last.current.body !== fingerprint) {
        last.current = { key: crypto.randomUUID(), body: fingerprint };
      }
      return last.current.key;
    },
    renew: () => {
      last.current = null;
    },
  };
}

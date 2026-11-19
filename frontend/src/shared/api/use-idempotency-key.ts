import { useState } from "react";

/**
 * One Idempotency-Key per intended action, made before the first send (SEC-19): a
 * repeated click or a retry sends the same key, so the server acts once. After the
 * action succeeds, renew it for the next one.
 *
 * Example:
 *   const { key, renew } = useIdempotencyKey();
 *   mutate({ params: { header: { "Idempotency-Key": key } } }, { onSuccess: renew });
 */
export function useIdempotencyKey() {
  const [key, setKey] = useState(() => crypto.randomUUID());
  return { key, renew: () => setKey(crypto.randomUUID()) };
}

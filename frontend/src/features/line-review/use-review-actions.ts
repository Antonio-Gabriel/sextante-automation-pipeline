import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { components as openapiComponents } from "../../../openapi.json";
import { $api } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/errors";
import { queryKeys } from "@/shared/api/query-keys";
import { useIdempotencyKey } from "@/shared/api/use-idempotency-key";
import { t, type MessageKey } from "@/shared/i18n/t";

// The limits come from the OpenAPI document, so they follow the server's (§8.4).
const correction = openapiComponents.schemas.CorrectionRequest.properties;
export const REVIEW_NOTE_MAX_LENGTH = correction.note.anyOf[0]?.maxLength ?? 0;

const reviewSchema = z.object({
  // An unchecked radio group is null in React Hook Form: no item chosen yet.
  item_number: z.string().regex(new RegExp(correction.item_number.pattern)).nullish(),
  note: z.string().trim().max(REVIEW_NOTE_MAX_LENGTH, { error: t("review.actions.noteTooLong") }),
});

type ReviewValues = z.input<typeof reviewSchema>;

/**
 * Accept or correct one coded line, each action with its own Idempotency-Key, made
 * before the first send (SEC-19). The server checks the item is in the line's sheet.
 *
 * Example:
 *   const actions = useReviewActions(encodedLineId);
 *   actions.accept();
 */
export function useReviewActions(encodedLineId: string) {
  const queryClient = useQueryClient();
  const acceptKey = useIdempotencyKey();
  const correctKey = useIdempotencyKey();
  const form = useForm<ReviewValues>({ resolver: zodResolver(reviewSchema), mode: "onBlur", defaultValues: { note: "" } });
  const done = (message: MessageKey, renew: () => void) => async () => {
    renew();
    form.reset({ note: "" });
    toast.success(t(message));
    await Promise.all(
      [queryKeys.allResults, queryKeys.allHistories, queryKeys.allCandidates, queryKeys.allInvoices].map(
        (queryKey) => queryClient.invalidateQueries({ queryKey }),
      ),
    );
  };
  const onError = (error: unknown) => {
    toast.error(errorMessage(error));
  };
  const acceptMutation = $api.useMutation("post", "/api/encoded-lines/{encoded_line_id}/accept", {
    onSuccess: done("review.actions.accepted", acceptKey.renew),
    onError,
  });
  const correctMutation = $api.useMutation("patch", "/api/encoded-lines/{encoded_line_id}", {
    onSuccess: done("review.actions.corrected", correctKey.renew),
    onError,
  });
  const path = { encoded_line_id: encodedLineId };
  const noteOrNull = (note: string) => (note.trim() === "" ? null : note.trim());
  return {
    form,
    chosenItem: form.watch("item_number") ?? undefined,
    remaining: REVIEW_NOTE_MAX_LENGTH - (form.watch("note") ?? "").length,
    isPending: acceptMutation.isPending || correctMutation.isPending,
    accept: form.handleSubmit(({ note }) =>
      acceptMutation.mutate({
        params: { path, header: { "Idempotency-Key": acceptKey.key } },
        body: { note: noteOrNull(note) },
      }),
    ),
    correct: form.handleSubmit(({ note, item_number: item }) => {
      if (item === undefined || item === null) return;
      correctMutation.mutate({
        params: { path, header: { "Idempotency-Key": correctKey.key } },
        body: { item_number: item, note: noteOrNull(note) },
      });
    }),
  };
}

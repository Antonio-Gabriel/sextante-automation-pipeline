import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { components as openapiComponents } from "../../../openapi.json";
import { $api } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/errors";
import { useIdempotencyKey } from "@/shared/api/use-idempotency-key";
import { useInvoiceChanged } from "@/shared/api/use-invoice-changed";
import { requireNumber } from "@/shared/format";
import { t, type MessageKey } from "@/shared/i18n/t";

// The limits come from the OpenAPI document, so they follow the server's (§8.4).
const correction = openapiComponents.schemas.CorrectionRequest.properties;
export const REVIEW_NOTE_MAX_LENGTH = requireNumber(
  correction.note.anyOf[0]?.maxLength,
  "CorrectionRequest.note.maxLength",
);

const reviewSchema = z.object({
  // An unchecked radio group is null in React Hook Form: no item chosen yet.
  item_number: z.string().regex(new RegExp(correction.item_number.pattern)).nullish(),
  note: z.string().trim().max(REVIEW_NOTE_MAX_LENGTH, { error: () => t("review.actions.noteTooLong") }),
});

type ReviewInput = z.input<typeof reviewSchema>;
type ReviewOutput = z.output<typeof reviewSchema>;

/**
 * Accept or correct one coded line. Each action keeps its key while its body is the
 * same (SEC-19); the server checks the item is in the line's sheet.
 *
 * Example:
 *   const actions = useReviewActions(encodedLineId);
 *   actions.accept();
 */
export function useReviewActions(encodedLineId: string) {
  const invoiceChanged = useInvoiceChanged();
  const acceptKeys = useIdempotencyKey();
  const correctKeys = useIdempotencyKey();
  const form = useForm<ReviewInput, unknown, ReviewOutput>({
    resolver: zodResolver(reviewSchema),
    mode: "onBlur",
    defaultValues: { note: "" },
  });
  const onActionDone = (message: MessageKey, renew: () => void) => async () => {
    renew();
    form.reset({ note: "" });
    toast.success(t(message));
    await invoiceChanged();
  };
  const onError = (error: unknown) => {
    toast.error(errorMessage(error));
  };
  const acceptMutation = $api.useMutation("post", "/api/encoded-lines/{encoded_line_id}/accept", {
    onSuccess: onActionDone("review.actions.accepted", acceptKeys.renew),
    onError,
  });
  const correctMutation = $api.useMutation("patch", "/api/encoded-lines/{encoded_line_id}", {
    onSuccess: onActionDone("review.actions.corrected", correctKeys.renew),
    onError,
  });
  const path = { encoded_line_id: encodedLineId };
  const noteOrNull = (note: string) => (note === "" ? null : note);
  const chosenItem = form.watch("item_number") ?? undefined;
  const isPending = acceptMutation.isPending || correctMutation.isPending;
  const failed = acceptMutation.error ?? correctMutation.error;
  return {
    register: form.register,
    noteError: form.formState.errors.note?.message,
    remaining: REVIEW_NOTE_MAX_LENGTH - (form.watch("note") ?? "").length,
    isPending,
    canCorrect: !isPending && chosenItem !== undefined,
    correctLabel:
      chosenItem === undefined
        ? t("review.actions.correctNone")
        : isPending
          ? t("review.actions.correcting")
          : t("review.actions.correct", { item: chosenItem }),
    // The last refusal, shown next to the actions as well as in the toast.
    failure: failed === null ? null : errorMessage(failed),
    accept: form.handleSubmit(({ note }) => {
      const body = { note: noteOrNull(note) };
      acceptMutation.mutate({ params: { path, header: { "Idempotency-Key": acceptKeys.keyFor(body) } }, body });
    }),
    correct: form.handleSubmit(({ note, item_number: item }) => {
      if (item === undefined || item === null) return;
      const body = { item_number: item, note: noteOrNull(note) };
      correctMutation.mutate({ params: { path, header: { "Idempotency-Key": correctKeys.keyFor(body) } }, body });
    }),
  };
}

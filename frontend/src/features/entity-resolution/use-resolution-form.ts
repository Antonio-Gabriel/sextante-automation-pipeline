import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { components as openapiComponents } from "../../../openapi.json";
import { RESOLUTIONS } from "@/entities/invoice/entity-resolutions";
import { $api } from "@/shared/api/client";
import { errorMessage, isKeyReused } from "@/shared/api/errors";
import { queryKeys } from "@/shared/api/query-keys";
import type { components } from "@/shared/api/schema";
import { useIdempotencyKey } from "@/shared/api/use-idempotency-key";
import { t } from "@/shared/i18n/t";

// The note's limits come from the OpenAPI document, so they follow the server's (§8.4).
const note = openapiComponents.schemas.EntityResolutionRequest.properties.note;
export const NOTE_MAX_LENGTH = note.maxLength;

const resolutionSchema = z.object({
  resolution: z.enum(RESOLUTIONS, { error: t("invoice.resolution.choiceRequired") }),
  note: z
    .string()
    .trim()
    .min(note.minLength, { error: t("invoice.resolution.noteRequired") })
    .max(NOTE_MAX_LENGTH, { error: t("invoice.resolution.noteTooLong") }),
}) satisfies z.ZodType<components["schemas"]["EntityResolutionRequest"]>;

type ResolutionInput = z.input<typeof resolutionSchema>;
type ResolutionOutput = z.output<typeof resolutionSchema>;

const AFFECTED = [queryKeys.allInvoices, queryKeys.allResults, queryKeys.allJobs];

/**
 * The resolution form of an ambiguous invoice: validated, sent once per key (SEC-19).
 *
 * Example:
 *   const { form, submit, isPending, remaining } = useResolutionForm(invoiceId, focusEntity);
 */
export function useResolutionForm(invoiceId: string, onResolved: () => void) {
  const queryClient = useQueryClient();
  const idempotency = useIdempotencyKey();
  const form = useForm<ResolutionInput, unknown, ResolutionOutput>({
    resolver: zodResolver(resolutionSchema),
    mode: "onBlur",
    defaultValues: { note: "" },
  });
  const refresh = () =>
    Promise.all(AFFECTED.map((queryKey) => queryClient.invalidateQueries({ queryKey })));
  const mutation = $api.useMutation("post", "/api/invoices/{invoice_id}/entity-resolution", {
    onSuccess: async () => {
      idempotency.renew();
      form.reset({ note: "" });
      toast.success(t("invoice.resolution.done"));
      await refresh();
      // The form leaves the page once resolved: focus goes where the result shows.
      onResolved();
    },
    onError: async (error) => {
      toast.error(errorMessage(error));
      // The key was spent on another body: a new attempt needs a new key, and the
      // invoice may already be resolved.
      if (isKeyReused(error)) {
        idempotency.renew();
        await refresh();
      }
    },
  });
  const submit = form.handleSubmit((values) =>
    mutation.mutate({
      params: { path: { invoice_id: invoiceId }, header: { "Idempotency-Key": idempotency.key } },
      body: values,
    }),
  );
  const remaining = NOTE_MAX_LENGTH - (form.watch("note") ?? "").length;
  return { form, submit, isPending: mutation.isPending, remaining };
}

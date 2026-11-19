import { zodResolver } from "@hookform/resolvers/zod";
import { useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { components as openapiComponents } from "../../../openapi.json";
import { $api } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/errors";
import { queryKeys } from "@/shared/api/query-keys";
import type { components } from "@/shared/api/schema";
import { useIdempotencyKey } from "@/shared/api/use-idempotency-key";
import { t } from "@/shared/i18n/t";

// The note's limit comes from the OpenAPI document, so it follows the server's (§8.4).
export const NOTE_MAX_LENGTH = openapiComponents.schemas.EntityResolutionRequest.properties.note.maxLength;

const resolutionSchema = z.object({
  resolution: z.enum(["MATCH", "NO_MATCH"], { error: t("invoice.resolution.choiceRequired") }),
  note: z
    .string()
    .trim()
    .min(1, { error: t("invoice.resolution.noteRequired") })
    .max(NOTE_MAX_LENGTH, { error: t("invoice.resolution.noteTooLong") }),
}) satisfies z.ZodType<components["schemas"]["EntityResolutionRequest"]>;

type ResolutionValues = z.input<typeof resolutionSchema>;

/**
 * The resolution form of an ambiguous invoice: validated, sent once per key (SEC-19).
 *
 * Example:
 *   const { form, submit, isPending, remaining } = useResolutionForm(invoiceId);
 */
export function useResolutionForm(invoiceId: string) {
  const queryClient = useQueryClient();
  const idempotency = useIdempotencyKey();
  const form = useForm<ResolutionValues>({
    resolver: zodResolver(resolutionSchema),
    mode: "onBlur",
    defaultValues: { note: "" },
  });
  const mutation = $api.useMutation("post", "/api/invoices/{invoice_id}/entity-resolution", {
    onSuccess: async () => {
      idempotency.renew();
      form.reset({ note: "" });
      toast.success(t("invoice.resolution.done"));
      await Promise.all(
        [queryKeys.allInvoices, queryKeys.allResults].map((queryKey) =>
          queryClient.invalidateQueries({ queryKey }),
        ),
      );
    },
    onError: (error) => {
      toast.error(errorMessage(error));
    },
  });
  const submit = form.handleSubmit((values) =>
    mutation.mutate({
      params: { path: { invoice_id: invoiceId }, header: { "Idempotency-Key": idempotency.key } },
      body: resolutionSchema.parse(values),
    }),
  );
  const remaining = NOTE_MAX_LENGTH - (form.watch("note") ?? "").length;
  return { form, submit, isPending: mutation.isPending, remaining };
}

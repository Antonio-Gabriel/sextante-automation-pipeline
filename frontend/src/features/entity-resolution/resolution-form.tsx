import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui-kit/card";
import { Label } from "@/shared/ui-kit/label";
import { Textarea } from "@/shared/ui-kit/textarea";

import { NOTE_MAX_LENGTH, useResolutionForm } from "./use-resolution-form";

const CHOICES = ["MATCH", "NO_MATCH"] as const;

/**
 * Resolve an ambiguous entity as the AMT or not, with a mandatory note.
 *
 * Example:
 *   <ResolutionForm invoiceId={invoiceId} />
 */
export function ResolutionForm({ invoiceId }: { invoiceId: string }) {
  const { form, submit, isPending, remaining } = useResolutionForm(invoiceId);
  const { errors } = form.formState;

  return (
    <Card className="border-amber-200">
      <CardHeader>
        <CardTitle>{t("invoice.resolution.title")}</CardTitle>
        <CardDescription>{t("invoice.resolution.description")}</CardDescription>
      </CardHeader>
      <CardContent>
        <form noValidate onSubmit={submit} className="flex flex-col gap-4">
          <fieldset className="flex flex-col gap-2">
            <legend className="mb-1 text-sm font-medium">{t("invoice.resolution.choice")}</legend>
            {CHOICES.map((choice) => (
              <label key={choice} className="flex items-center gap-2 text-sm">
                <input type="radio" value={choice} className="accent-brand-700" {...form.register("resolution")} />
                {t(`invoice.resolution.${choice}`)}
              </label>
            ))}
            {errors.resolution?.message !== undefined && (
              <p role="alert" className="text-sm text-red-700">{errors.resolution.message}</p>
            )}
          </fieldset>
          <div className="flex flex-col gap-2">
            <Label htmlFor="resolution-note">{t("invoice.resolution.note")}</Label>
            <Textarea
              id="resolution-note"
              rows={3}
              maxLength={NOTE_MAX_LENGTH}
              aria-invalid={errors.note !== undefined}
              aria-describedby="resolution-note-help"
              {...form.register("note")}
            />
            <p id="resolution-note-help" className="text-xs text-slate-500">
              {t("invoice.resolution.remaining", { count: remaining })}
            </p>
            {errors.note?.message !== undefined && (
              <p role="alert" className="text-sm text-red-700">{errors.note.message}</p>
            )}
          </div>
          <Button type="submit" className="self-start" disabled={isPending}>
            {isPending ? t("invoice.resolution.submitting") : t("invoice.resolution.submit")}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

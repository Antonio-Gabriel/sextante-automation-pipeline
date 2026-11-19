import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui-kit/card";
import { Label } from "@/shared/ui-kit/label";
import { Textarea } from "@/shared/ui-kit/textarea";

import { REVIEW_NOTE_MAX_LENGTH, type useReviewActions } from "./use-review-actions";

interface ReviewActionsProps {
  actions: ReturnType<typeof useReviewActions>;
  pending: boolean;
}

/**
 * The note and the two decisions: accept a pending line, or correct its code to the
 * item chosen in the table.
 *
 * Example:
 *   <ReviewActions actions={actions} pending={line.review_status === "pending"} />
 */
export function ReviewActions({ actions, pending }: ReviewActionsProps) {
  const { form, isPending, chosenItem, remaining } = actions;
  const noteError = form.formState.errors.note?.message;
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("review.actions.title")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <Label htmlFor="review-note">{t("review.actions.note")}</Label>
          <Textarea
            id="review-note"
            rows={3}
            maxLength={REVIEW_NOTE_MAX_LENGTH}
            aria-invalid={noteError !== undefined}
            aria-describedby={noteError === undefined ? "review-note-help" : "review-note-help review-note-error"}
            {...form.register("note")}
          />
          <p id="review-note-help" className="text-xs text-slate-500">
            {t("review.actions.remaining", { count: remaining })}
          </p>
          {noteError !== undefined && (
            <p id="review-note-error" role="alert" className="text-sm text-red-700">
              {noteError}
            </p>
          )}
        </div>
        {!pending && <p className="text-sm text-slate-500">{t("review.actions.notPending")}</p>}
        <div className="flex flex-wrap gap-2">
          {pending && (
            <Button variant="outline" disabled={isPending} onClick={() => void actions.accept()}>
              {isPending ? t("review.actions.accepting") : t("review.actions.accept")}
            </Button>
          )}
          <Button disabled={isPending || chosenItem === undefined} onClick={() => void actions.correct()}>
            {chosenItem === undefined
              ? t("review.actions.correctNone")
              : isPending
                ? t("review.actions.correcting")
                : t("review.actions.correct", { item: chosenItem })}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

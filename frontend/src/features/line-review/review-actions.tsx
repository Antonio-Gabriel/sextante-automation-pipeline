import type { UseFormRegister } from "react-hook-form";

import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui-kit/card";
import { Label } from "@/shared/ui-kit/label";
import { Textarea } from "@/shared/ui-kit/textarea";

import { REVIEW_NOTE_MAX_LENGTH } from "./use-review-actions";

interface ReviewActionsProps {
  registerNote: ReturnType<UseFormRegister<{ note: string }>>;
  noteError: string | undefined;
  remaining: number;
  /** Whether the line's review is still pending: only then is acceptance offered. */
  reviewPending: boolean;
  isPending: boolean;
  canCorrect: boolean;
  correctLabel: string;
  failure: string | null;
  onAccept: () => void;
  onCorrect: () => void;
}

/**
 * The note and the two decisions: accept a pending line, or correct its code to the
 * item chosen in the table.
 *
 * Example:
 *   <ReviewActions {...props} />
 */
export function ReviewActions(props: ReviewActionsProps) {
  const { noteError } = props;
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
            {...props.registerNote}
          />
          <p id="review-note-help" aria-live="polite" className="text-xs text-slate-500">
            {t("review.actions.remaining", { count: props.remaining })}
          </p>
          {noteError !== undefined && (
            <p id="review-note-error" role="alert" className="text-sm text-red-700">
              {noteError}
            </p>
          )}
        </div>
        {!props.reviewPending && <p className="text-sm text-slate-500">{t("review.actions.notPending")}</p>}
        <div className="flex flex-wrap gap-2">
          {props.reviewPending && (
            <Button variant="outline" disabled={props.isPending} onClick={props.onAccept}>
              {props.isPending ? t("review.actions.accepting") : t("review.actions.accept")}
            </Button>
          )}
          <Button disabled={!props.canCorrect} onClick={props.onCorrect}>
            {props.correctLabel}
          </Button>
        </div>
        {props.failure !== null && (
          <p role="alert" className="text-sm text-red-700">
            {props.failure}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

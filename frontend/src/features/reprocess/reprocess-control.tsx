import { RotateCcw } from "lucide-react";

import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";

import { useConfirmationFocus } from "@/shared/ui-kit/use-confirmation-focus";
import { useReprocess } from "./use-reprocess";

/**
 * The reprocessing of one invoice, behind a confirmation that warns what it replaces.
 * Focus starts on the safe choice, stays in the confirmation, and returns to the button.
 *
 * Example:
 *   <ReprocessControl invoiceId={invoiceId} />
 */
export function ReprocessControl({ invoiceId }: { invoiceId: string }) {
  const reprocess = useReprocess(invoiceId);
  const focus = useConfirmationFocus(reprocess.confirming, reprocess.cancel);

  if (!reprocess.confirming) {
    return (
      <Button ref={focus.trigger} variant="outline" className="self-start" onClick={reprocess.ask}>
        <RotateCcw />
        {t("reprocess.action")}
      </Button>
    );
  }
  return (
    <div
      ref={focus.dialog}
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="reprocess-title"
      aria-describedby="reprocess-body"
      onKeyDown={focus.onKeyDown}
      className="flex max-w-xl flex-col gap-3 rounded-xl border border-amber-300 bg-amber-50 p-4"
    >
      <p id="reprocess-title" className="font-semibold text-amber-900">{t("reprocess.confirmTitle")}</p>
      <p id="reprocess-body" className="text-sm text-amber-900">{t("reprocess.confirmBody")}</p>
      <div className="flex gap-2">
        <Button ref={focus.safeChoice} variant="ghost" disabled={reprocess.isPending} onClick={reprocess.cancel}>
          {t("reprocess.cancel")}
        </Button>
        <Button disabled={reprocess.isPending} onClick={reprocess.confirm}>
          {reprocess.isPending ? t("reprocess.sending") : t("reprocess.confirm")}
        </Button>
      </div>
    </div>
  );
}

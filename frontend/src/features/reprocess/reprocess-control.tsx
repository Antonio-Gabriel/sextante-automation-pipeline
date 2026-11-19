import { RotateCcw } from "lucide-react";
import { useEffect, useRef } from "react";

import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";

import { useReprocess } from "./use-reprocess";

/**
 * The reprocessing of one invoice, behind a confirmation that warns what it replaces.
 *
 * Example:
 *   <ReprocessControl invoiceId={invoiceId} />
 */
export function ReprocessControl({ invoiceId }: { invoiceId: string }) {
  const reprocess = useReprocess(invoiceId);
  const confirmButton = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    if (reprocess.asking) confirmButton.current?.focus();
  }, [reprocess.asking]);

  if (!reprocess.asking) {
    return (
      <Button variant="outline" onClick={reprocess.ask}>
        <RotateCcw />
        {t("reprocess.action")}
      </Button>
    );
  }
  return (
    <div
      role="alertdialog"
      aria-labelledby="reprocess-title"
      aria-describedby="reprocess-body"
      onKeyDown={(event) => event.key === "Escape" && reprocess.cancel()}
      className="flex max-w-xl flex-col gap-3 rounded-xl border border-amber-300 bg-amber-50 p-4"
    >
      <p id="reprocess-title" className="font-semibold text-amber-900">{t("reprocess.confirmTitle")}</p>
      <p id="reprocess-body" className="text-sm text-amber-900">{t("reprocess.confirmBody")}</p>
      <div className="flex gap-2">
        <Button ref={confirmButton} disabled={reprocess.isPending} onClick={reprocess.confirm}>
          {reprocess.isPending ? t("reprocess.sending") : t("reprocess.confirm")}
        </Button>
        <Button variant="ghost" disabled={reprocess.isPending} onClick={reprocess.cancel}>
          {t("reprocess.cancel")}
        </Button>
      </div>
    </div>
  );
}

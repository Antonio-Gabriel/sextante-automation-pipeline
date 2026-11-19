import { useRouter } from "@tanstack/react-router";
import { RotateCw, ServerCrash } from "lucide-react";

import { errorMessage } from "@/shared/api/errors";
import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";

/**
 * What a page shows when it cannot load, for instance when the server cannot be reached:
 * the reason in the language in force and a way to try again, never a blank screen.
 *
 * Example:
 *   createRouter({ routeTree, defaultErrorComponent: RouteError })
 */
export function RouteError({ error }: { error: unknown }) {
  const router = useRouter();
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <div role="alert" className="flex max-w-md flex-col items-center gap-3 rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-xs">
        <span className="flex size-12 items-center justify-center rounded-full bg-red-50 text-red-600">
          <ServerCrash className="size-6" aria-hidden />
        </span>
        <h1 className="text-lg font-semibold text-slate-900">{t("errors.pageTitle")}</h1>
        <p className="text-sm text-slate-600">{errorMessage(error)}</p>
        <Button className="mt-2" onClick={() => void router.invalidate()}>
          <RotateCw />
          {t("errors.retry")}
        </Button>
      </div>
    </main>
  );
}

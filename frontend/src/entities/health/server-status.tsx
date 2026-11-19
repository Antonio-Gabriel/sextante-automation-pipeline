import { t } from "@/shared/i18n/t";
import { cn } from "@/shared/ui-kit/cn";

import { useHealth, type HealthState } from "./use-health";

const DOT: Record<HealthState, string> = {
  loading: "bg-slate-300",
  up: "bg-emerald-500",
  down: "bg-red-500",
};

/** The server's state and the catalog version it serves, in the sidebar. */
export function ServerStatus() {
  const health = useHealth();
  return (
    <dl className="grid grid-cols-[max-content_1fr] gap-x-3 gap-y-1 text-xs">
      <dt className="text-slate-500">{t("health.server")}</dt>
      <dd className="flex items-center gap-1.5 text-slate-700">
        <span aria-hidden className={cn("size-2 rounded-full", DOT[health.state])} />
        {t(health.label)}
      </dd>
      <dt className="text-slate-500">{t("health.catalog")}</dt>
      <dd className="truncate font-mono text-slate-700" title={health.catalogDigest}>
        {health.catalogDigest?.slice(0, 12) ?? t("health.notAvailable")}
      </dd>
    </dl>
  );
}

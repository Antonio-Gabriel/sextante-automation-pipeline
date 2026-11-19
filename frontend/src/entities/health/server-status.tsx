import { shortDigest } from "@/shared/format";
import { t } from "@/shared/i18n/t";
import { cn } from "@/shared/ui-kit/cn";

import { useHealth } from "./use-health";

/** The server's state and the catalog version it serves, in the sidebar. */
export function ServerStatus() {
  const health = useHealth();
  return (
    <dl className="grid grid-cols-[max-content_1fr] gap-x-3 gap-y-1 text-xs">
      <dt className="text-slate-500">{t("health.server")}</dt>
      <dd className="flex items-center gap-1.5 text-slate-700">
        <span aria-hidden className={cn("size-2 rounded-full", health.dot)} />
        {t(health.label)}
      </dd>
      <dt className="text-slate-500">{t("health.catalog")}</dt>
      <dd className="truncate font-mono text-slate-700" title={health.catalogDigest}>
        {health.catalogDigest === undefined ? t("health.notAvailable") : shortDigest(health.catalogDigest)}
      </dd>
    </dl>
  );
}

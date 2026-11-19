import { Link, Outlet } from "@tanstack/react-router";
import { History, Upload } from "lucide-react";

import logo from "@/assets/amt-logo.png";
import { useRecentJobs } from "@/entities/job/recent-jobs";
import { ServerStatus } from "@/entities/health/server-status";
import { LogoutButton } from "@/features/auth/logout-button";
import { t } from "@/shared/i18n/t";

const NAV_LINK =
  "flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900 [&_svg]:size-4";
const NAV_ACTIVE = "bg-brand-50 text-brand-700 hover:bg-brand-50 hover:text-brand-700";

/** The panel: sidebar with the AMT logo and navigation, the page beside it. */
export function AppShell() {
  return (
    <div className="flex min-h-screen">
      <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="flex h-16 items-center border-b border-slate-200 px-5">
          <img src={logo} alt={t("app.logoAlt")} className="h-9 w-auto" />
        </div>
        <nav aria-label={t("nav.main")} className="flex flex-1 flex-col gap-6 overflow-y-auto p-3">
          <Link to="/" className={NAV_LINK} activeProps={{ className: NAV_ACTIVE }} activeOptions={{ exact: true }}>
            <Upload />
            {t("nav.upload")}
          </Link>
          <RecentJobs />
        </nav>
        <div className="flex flex-col gap-3 border-t border-slate-200 p-4">
          <ServerStatus />
          <LogoutButton />
        </div>
      </aside>
      <div className="min-w-0 flex-1">
        <Outlet />
      </div>
    </div>
  );
}

function RecentJobs() {
  const jobIds = useRecentJobs((state) => state.jobIds);
  return (
    <div className="flex flex-col gap-1">
      <p className="flex items-center gap-2 px-3 text-xs font-medium uppercase tracking-wide text-slate-400 [&_svg]:size-3.5">
        <History />
        {t("nav.recentJobs")}
      </p>
      {jobIds.length === 0 ? (
        <p className="px-3 py-1 text-sm text-slate-400">{t("nav.noRecentJobs")}</p>
      ) : (
        jobIds.map((jobId) => (
          <Link
            key={jobId}
            to="/jobs/$jobId"
            params={{ jobId }}
            className={`${NAV_LINK} font-mono text-xs`}
            activeProps={{ className: NAV_ACTIVE }}
          >
            {jobId.slice(0, 8)}
          </Link>
        ))
      )}
    </div>
  );
}

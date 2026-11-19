import { useHealth } from "@/entities/health/use-health";
import { LogoutButton } from "@/features/auth/logout-button";
import { t } from "@/shared/i18n/t";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui-kit/card";

export function HomePage() {
  return (
    <main className="mx-auto flex max-w-3xl flex-col gap-6 p-6">
      <header className="flex items-center justify-between">
        <div>
          <p className="text-xl font-semibold">{t("app.name")}</p>
          <p className="text-sm text-slate-500">{t("app.tagline")}</p>
        </div>
        <LogoutButton />
      </header>
      <ServerStatusCard />
    </main>
  );
}

function ServerStatusCard() {
  const health = useHealth();

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("home.title")}</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-[max-content_1fr] gap-x-6 gap-y-2 text-sm">
          <dt className="text-slate-500">{t("home.serverStatus")}</dt>
          <dd>{t(health.status)}</dd>
          <dt className="text-slate-500">{t("home.catalogDigest")}</dt>
          <dd className="break-all font-mono">{health.catalogDigest ?? t("home.notAvailable")}</dd>
        </dl>
      </CardContent>
    </Card>
  );
}

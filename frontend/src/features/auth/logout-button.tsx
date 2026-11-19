import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";

import { useLogout } from "./use-logout";

export function LogoutButton() {
  const logout = useLogout();
  return (
    <Button variant="outline" size="sm" disabled={logout.isPending} onClick={() => logout.mutate({})}>
      {logout.isPending ? t("home.loggingOut") : t("home.logout")}
    </Button>
  );
}

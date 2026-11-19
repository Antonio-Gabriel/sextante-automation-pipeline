import { LogOut } from "lucide-react";

import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";

import { useLogout } from "./use-logout";

export function LogoutButton() {
  const logout = useLogout();
  return (
    <Button
      variant="outline"
      size="sm"
      className="w-full"
      disabled={logout.isPending}
      onClick={() => logout.mutate({})}
    >
      <LogOut />
      {logout.isPending ? t("session.loggingOut") : t("session.logout")}
    </Button>
  );
}

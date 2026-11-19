import { Outlet } from "@tanstack/react-router";
import { Toaster } from "sonner";

import { useSessionExpiry } from "@/features/auth/use-session-expiry";

export function RootLayout() {
  useSessionExpiry();
  return (
    <>
      <Outlet />
      <Toaster richColors position="top-right" />
    </>
  );
}

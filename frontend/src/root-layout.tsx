import { Outlet } from "@tanstack/react-router";
import { useEffect } from "react";
import { Toaster } from "sonner";

import { useSessionExpiry } from "@/features/auth/use-session-expiry";
import { useLanguage } from "@/shared/i18n/language";

export function RootLayout() {
  useSessionExpiry();
  const language = useLanguage((state) => state.language);
  useEffect(() => {
    document.documentElement.lang = language === "pt" ? "pt-PT" : "en";
  }, [language]);
  return (
    <>
      {/* A new language draws every text again: the pages are mounted anew in it. */}
      <Outlet key={language} />
      <Toaster richColors position="top-right" />
    </>
  );
}

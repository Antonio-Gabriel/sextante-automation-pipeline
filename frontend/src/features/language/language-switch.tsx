import { useQueryClient } from "@tanstack/react-query";
import { Languages } from "lucide-react";

import { LANGUAGES, useLanguage, type Language } from "@/shared/i18n/language";
import { t } from "@/shared/i18n/t";
import { cn } from "@/shared/ui-kit/cn";

/**
 * English or Portuguese, for the whole interface and the server's texts. Each name is
 * written in its own language, so a person finds theirs whichever is in force.
 *
 * Example:
 *   <LanguageSwitch />
 */
export function LanguageSwitch({ className }: { className?: string }) {
  const { language, setLanguage } = useLanguage();
  const queryClient = useQueryClient();
  const choose = (next: Language) => {
    if (next === language) return;
    setLanguage(next);
    // Flags, reasons and catalog descriptions come from the server in the language asked.
    void queryClient.invalidateQueries();
  };
  return (
    <div role="group" aria-label={t("language.label")} className={cn("flex items-center gap-2", className)}>
      <Languages className="size-4 text-slate-400" aria-hidden />
      <div className="flex rounded-lg border border-slate-200 bg-slate-50 p-0.5">
        {LANGUAGES.map((option) => (
          <button
            key={option}
            type="button"
            lang={option}
            aria-pressed={option === language}
            onClick={() => choose(option)}
            className={cn(
              "rounded-md px-2.5 py-1 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400",
              option === language ? "bg-white text-brand-700 shadow-xs ring-1 ring-slate-200" : "text-slate-500 hover:text-slate-800",
            )}
          >
            {t(`language.${option}`)}
          </button>
        ))}
      </div>
    </div>
  );
}

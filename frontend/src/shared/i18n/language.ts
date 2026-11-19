import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

// The interface language (D-3.25): English by default, Portuguese on request. A view
// preference of this browser (§8.3); the server answers in it through Accept-Language.
export const LANGUAGES = ["en", "pt"] as const;
export type Language = (typeof LANGUAGES)[number];
export const DEFAULT_LANGUAGE: Language = "en";

const LOCALES: Record<Language, string> = { en: "en-GB", pt: "pt-PT" };

interface LanguageState {
  language: Language;
  setLanguage: (language: Language) => void;
}

export const useLanguage = create<LanguageState>()(
  persist(
    (set) => ({
      language: DEFAULT_LANGUAGE,
      setLanguage: (language) => set({ language }),
    }),
    {
      name: "sextante-language",
      storage: createJSONStorage(() => localStorage),
      // A stored value from elsewhere is ignored rather than trusted.
      merge: (stored, current) => {
        const language = typeof stored === "object" && stored !== null ? Reflect.get(stored, "language") : undefined;
        return LANGUAGES.includes(language) ? { ...current, language } : current;
      },
    },
  ),
);

/** The language in force, read outside React (the HTTP client, formatting, `t`). */
export function currentLanguage(): Language {
  return useLanguage.getState().language;
}

/** The locale numbers and dates are formatted in for the language in force. */
export function currentLocale(): string {
  return LOCALES[currentLanguage()];
}

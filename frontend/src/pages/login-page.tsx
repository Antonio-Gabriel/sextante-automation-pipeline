import logo from "@/assets/amt-logo.png";
import { LoginForm } from "@/features/auth/login-form";
import { LanguageSwitch } from "@/features/language/language-switch";
import { t } from "@/shared/i18n/t";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui-kit/card";

export function LoginPage() {
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center gap-8 bg-gradient-to-b from-brand-50 to-slate-50 p-4">
      <LanguageSwitch className="absolute right-4 top-4" />
      <div className="flex flex-col items-center gap-2 text-center">
        <img src={logo} alt={t("app.logoAlt")} className="h-16 w-auto" />
        <p className="text-sm text-slate-500">{t("app.tagline")}</p>
      </div>
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>{t("login.title")}</CardTitle>
          <CardDescription>{t("login.description")}</CardDescription>
        </CardHeader>
        <CardContent>
          <LoginForm />
        </CardContent>
      </Card>
    </main>
  );
}

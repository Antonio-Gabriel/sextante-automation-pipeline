import { LoginForm } from "@/features/auth/login-form";
import { t } from "@/shared/i18n/t";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/ui-kit/card";

export function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-4">
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

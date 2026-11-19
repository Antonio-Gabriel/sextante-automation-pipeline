import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { components as openapiComponents } from "../../../openapi.json";
import type { components } from "@/shared/api/schema";
import { t } from "@/shared/i18n/t";
import { Button } from "@/shared/ui-kit/button";
import { Input } from "@/shared/ui-kit/input";
import { Label } from "@/shared/ui-kit/label";

import { useLogin } from "./use-login";

// The limit comes from the OpenAPI document, so it follows the server's (§8.4).
const TOKEN_MAX_LENGTH = openapiComponents.schemas.AccessTokenRequest.properties.token.maxLength;

const loginSchema = z.object({
  token: z
    .string()
    .min(1, { error: () => t("login.tokenRequired") })
    .max(TOKEN_MAX_LENGTH, { error: () => t("login.tokenTooLong") }),
}) satisfies z.ZodType<components["schemas"]["AccessTokenRequest"]>;

type LoginValues = z.infer<typeof loginSchema>;

export function LoginForm() {
  const login = useLogin();
  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    mode: "onBlur",
    defaultValues: { token: "" },
  });
  const tokenError = form.formState.errors.token?.message;

  return (
    <form
      noValidate
      className="flex flex-col gap-4"
      onSubmit={form.handleSubmit((values) => login.mutate({ body: values }))}
    >
      <div className="flex flex-col gap-2">
        <Label htmlFor="token">{t("login.tokenLabel")}</Label>
        <Input
          id="token"
          type="password"
          autoComplete="current-password"
          aria-invalid={tokenError !== undefined}
          aria-describedby={tokenError === undefined ? undefined : "token-error"}
          {...form.register("token")}
        />
        {tokenError !== undefined && (
          <p id="token-error" role="alert" className="text-sm text-red-700">
            {tokenError}
          </p>
        )}
      </div>
      <Button type="submit" disabled={login.isPending}>
        {login.isPending ? t("login.submitting") : t("login.submit")}
      </Button>
    </form>
  );
}

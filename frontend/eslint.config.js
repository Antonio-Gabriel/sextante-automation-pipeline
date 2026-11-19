import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "src/shared/api/schema.d.ts"] },
  {
    files: ["**/*.{ts,tsx}"],
    extends: [js.configs.recommended, ...tseslint.configs.strict],
    languageOptions: { globals: globals.browser },
    plugins: { "react-hooks": reactHooks },
    rules: {
      ...reactHooks.configs.recommended.rules,
      // 04-padroes-de-codigo.md §8: no any, and no dangerouslySetInnerHTML (CLAUDE.md).
      "@typescript-eslint/no-explicit-any": "error",
      "no-restricted-syntax": [
        "error",
        {
          selector: "JSXAttribute[name.name='dangerouslySetInnerHTML']",
          message: "dangerouslySetInnerHTML is forbidden in this project.",
        },
      ],
    },
  },
);

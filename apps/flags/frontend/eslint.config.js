import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "node_modules", ".venv"] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2021,
      globals: globals.browser,
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
    },
  },
  {
    // Boundary: app frontends must go through the platform kit — no raw
    // network calls, no reaching into another app.
    files: ["src/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-globals": [
        "error",
        { name: "fetch", message: "Apps must use the platform API client (@platform/api/client)." },
        { name: "XMLHttpRequest", message: "Apps must use the platform API client." },
      ],
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            { group: ["axios", "ky", "superagent"], message: "Apps must use the platform API client." },
            { group: ["../../../apps/*"], message: "Apps must not import from other apps." },
          ],
        },
      ],
    },
  },
);

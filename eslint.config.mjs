import js from "@eslint/js";

export default [
  {
    ignores: ["**/node_modules/**", "**/dist/**", "**/build/**", "**/.expo/**"]
  },
  js.configs.recommended,
  {
    files: ["apps/frontend/**/*.{js,jsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module"
    },
    rules: {
      "no-console": "off"
    }
  }
];

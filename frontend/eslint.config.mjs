import js from "@eslint/js";
import tsPlugin from "typescript-eslint";

export default [
  js.configs.recommended,
  ...tsPlugin.configs.recommended,
  {
    rules: {
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "off"
    }
  },
  {
    ignores: [".next/", "node_modules/", "coverage/"]
  }
];


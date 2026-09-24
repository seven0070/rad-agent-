// eslint.config.js — flat config (ESLint 10).
//
// The no-inline-style rule gates NEW `style={{...}}` attributes; the ~286
// pre-existing violations are owned by the F3 codemod and will clear as it
// lands. Run `npm run lint` to count them.
import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist/**", "node_modules/**", "src-tauri/**"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector: 'JSXAttribute[name.name="style"]',
          message: "Static inline style={{...}} is banned; use design-system classes/tokens.",
        },
      ],
    },
  },
);

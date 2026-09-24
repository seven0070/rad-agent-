import { defineConfig } from "vitest/config";
export default defineConfig({
  test: {
    environment: "node",
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    // React DOM tests need jsdom; jsdom workers hang on the Google Drive
    // path. Run Button.test.tsx via vite.config.ts (or a C:-side copy).
    exclude: ["**/node_modules/**", "**/Button.test.tsx"],
    setupFiles: ["src/test/setup-node.ts"],
    pool: "threads",
    fileParallelism: false,
    testTimeout: 15000,
  },
});


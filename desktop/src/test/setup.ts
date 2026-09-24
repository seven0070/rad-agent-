/**
 * Global Vitest setup (wired via `test.setupFiles` in vite.config.ts).
 *
 * Tests run in plain jsdom — NOT inside the Tauri shell. `src/backend.ts`
 * only dynamically imports `@tauri-apps/api/core` when `isTauri()` is true,
 * i.e. when `window.__TAURI_INTERNALS__` exists. We keep that flag ABSENT by
 * default so every test exercises the non-Tauri fallback path.
 *
 * Tests that need the shell must BOTH:
 *   1. `vi.mock("@tauri-apps/api/core", () => ({ invoke: vi.fn() }))`, and
 *   2. set `window.__TAURI_INTERNALS__ = {}` for the duration of the test.
 * See `src/backend.tauri.test.ts` — it FAILS if the mock is removed.
 */
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// React 18 requires this flag for `act()` outside a real test framework
// globals setup; set it defensively so component tests never warn.
Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

afterEach(() => {
  cleanup();
  // Never leak a fake Tauri shell between tests.
  delete (window as { __TAURI_INTERNALS__?: unknown }).__TAURI_INTERNALS__;
});

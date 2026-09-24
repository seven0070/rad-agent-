/**
 * Node-env polyfill for Vitest when jsdom is unusable (Google Drive path).
 * Provides just enough `window` + `localStorage` for non-Tauri fallback tests.
 * When a file opts into jsdom (`environmentMatchGlobs` for `*.tsx`), also
 * runs RTL cleanup so component tests don't leak between cases.
 */
import { afterEach } from "vitest";

const g = globalThis as Record<string, unknown>;

if (typeof g.window === "undefined") {
  g.window = g;
}

if (typeof g.localStorage === "undefined") {
  const store = new Map<string, string>();
  g.localStorage = {
    getItem: (k: string) => (store.has(String(k)) ? store.get(String(k))! : null),
    setItem: (k: string, v: string) => {
      store.set(String(k), String(v));
    },
    removeItem: (k: string) => {
      store.delete(String(k));
    },
    clear: () => store.clear(),
    key: (i: number) => [...store.keys()][i] ?? null,
    get length() {
      return store.size;
    },
  };
}

Object.assign(globalThis, { IS_REACT_ACT_ENVIRONMENT: true });

afterEach(() => {
  const w = g.window as { __TAURI_INTERNALS__?: unknown };
  if (w && typeof w === "object") {
    delete w.__TAURI_INTERNALS__;
  }
});

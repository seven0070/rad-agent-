/**
 * Non-Tauri fallback path of src/backend.ts — no shell, no sidecar, no mock.
 *
 * Deliberately NO `vi.mock("@tauri-apps/api/core")` here: these tests must
 * pass while the real Tauri module is never imported (isTauri() is false in
 * plain jsdom, so the dynamic import in backend.ts never executes).
 */
import { describe, expect, it } from "vitest";
import {
  apiBase,
  apiToken,
  backendHealth,
  backendInfo,
  backendStart,
  clearStoredConnection,
  getStoredConnection,
  isTauri,
  saveStoredConnection,
} from "./backend";

describe("backend.ts non-Tauri fallback", () => {
  it("detects no Tauri shell in jsdom", () => {
    expect(isTauri()).toBe(false);
  });

  it("backendStart/backendInfo/backendHealth degrade gracefully", async () => {
    await expect(backendStart(7456)).resolves.toEqual({
      running: false,
      port: 7456,
      home: "",
      pid: null,
      managed: false,
      sidecar: false,
    });
    await expect(backendInfo()).resolves.toEqual({
      running: false,
      port: 7331,
      home: "",
      pid: null,
      managed: false,
      sidecar: false,
    });
    await expect(backendHealth(7456)).resolves.toEqual({
      ok: false,
      port: 7456,
      error: "not managed by desktop",
    });
  });

  it("apiToken falls back to env/empty without the shell", async () => {
    // VITE_RAD_TOKEN is not set in the test environment.
    await expect(apiToken("/nowhere")).resolves.toBe("");
  });

  it("apiBase defaults to loopback:port", () => {
    expect(apiBase(7331)).toBe("http://127.0.0.1:7331");
  });

  it("stored connection round-trips", () => {
    saveStoredConnection("http://127.0.0.1:7331", "tok");
    expect(getStoredConnection()).toEqual({ base: "http://127.0.0.1:7331", token: "tok" });
    clearStoredConnection();
    expect(getStoredConnection()).toEqual({ base: "", token: "" });
  });
});

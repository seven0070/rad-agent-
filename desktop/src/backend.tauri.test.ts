/**
 * Tauri-shell path of src/backend.ts, with `@tauri-apps/api/core` mocked.
 *
 * PROOF OF MOCK — these tests FAIL if the `vi.mock("@tauri-apps/api/core", …)`
 * factory below is removed:
 *   - `invoke` would be the real Tauri function, so
 *     `expect(vi.isMockFunction(invoke)).toBe(true)` fails, and
 *   - the real invoke would throw/misbehave against the bare
 *     `window.__TAURI_INTERNALS__ = {}` stub, failing the command assertions.
 * The invoke-mock guard test below makes the dependency explicit.
 */
import { invoke } from "@tauri-apps/api/core";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { backendHealth, backendInfo, backendStart, defaultHome } from "./backend";

vi.mock("@tauri-apps/api/core", () => ({
  invoke: vi.fn(),
}));

const invokeMock = vi.mocked(invoke);
const win = window as unknown as { __TAURI_INTERNALS__?: Record<string, unknown> };

describe("backend.ts under a (mocked) Tauri shell", () => {
  beforeEach(() => {
    win.__TAURI_INTERNALS__ = {}; // pretend we run inside Tauri
    invokeMock.mockReset();
  });

  afterEach(() => {
    delete win.__TAURI_INTERNALS__;
  });

  it("the @tauri-apps/api invoke mock is applied (shell-independence guard)", () => {
    // If the vi.mock factory above is removed, this assertion fails.
    expect(vi.isMockFunction(invoke)).toBe(true);
  });

  it("backendInfo() proxies to the backend_info command", async () => {
    const info = {
      running: true,
      port: 7331,
      home: "/home/u/.rad",
      pid: 42,
      managed: true,
      sidecar: true,
    };
    invokeMock.mockResolvedValue(info);

    await expect(backendInfo()).resolves.toEqual(info);
    expect(invokeMock).toHaveBeenCalledWith("backend_info", undefined);
  });

  it("backendHealth() and backendStart() proxy their commands", async () => {
    invokeMock.mockResolvedValueOnce({ ok: true, port: 7331, version: "0.1" });
    await expect(backendHealth(7331)).resolves.toEqual({ ok: true, port: 7331, version: "0.1" });
    expect(invokeMock).toHaveBeenLastCalledWith("backend_health", { port: 7331 });

    invokeMock.mockResolvedValueOnce({
      running: true,
      port: 7331,
      home: "",
      pid: 1,
      managed: true,
      sidecar: true,
    });
    await backendStart(7331);
    expect(invokeMock).toHaveBeenLastCalledWith("backend_start", { port: 7331, home: null });
  });

  it("defaultHome() proxies the default_home command", async () => {
    invokeMock.mockResolvedValueOnce("/home/u/.rad");
    await expect(defaultHome()).resolves.toBe("/home/u/.rad");
    expect(invokeMock).toHaveBeenCalledWith("default_home", undefined);
  });
});

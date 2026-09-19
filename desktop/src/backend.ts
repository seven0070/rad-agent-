/** Tauri commands for RAD backend lifecycle. Fixed sidecar argv only — no user shell. */

export interface BackendInfo {
  running: boolean;
  port: number;
  home: string;
  pid: number | null;
  managed: boolean;
  sidecar: boolean;
}

export interface BackendHealth {
  ok: boolean;
  port: number;
  version?: string;
  error?: string;
}

export type ConnState = "connecting" | "connected" | "reconnecting" | "down";

function isTauri(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

async function invoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  const { invoke: inv } = await import("@tauri-apps/api/core");
  return inv<T>(cmd, args);
}

export { isTauri };

export async function backendStart(port = 7331, home?: string): Promise<BackendInfo> {
  if (!isTauri()) {
    return { running: false, port, home: home || "", pid: null, managed: false, sidecar: false };
  }
  return invoke<BackendInfo>("backend_start", { port, home: home ?? null });
}

export async function backendStop(): Promise<void> {
  if (!isTauri()) return;
  await invoke("backend_stop");
}

export async function backendRestart(port = 7331, home?: string): Promise<BackendInfo> {
  if (!isTauri()) {
    return { running: false, port, home: home || "", pid: null, managed: false, sidecar: false };
  }
  return invoke<BackendInfo>("backend_restart", { port, home: home ?? null });
}

export async function backendInfo(): Promise<BackendInfo> {
  if (!isTauri()) {
    return { running: false, port: 7331, home: "", pid: null, managed: false, sidecar: false };
  }
  return invoke<BackendInfo>("backend_info");
}

export async function backendHealth(port = 7331): Promise<BackendHealth> {
  if (!isTauri()) {
    return { ok: false, port, error: "not managed by desktop" };
  }
  return invoke<BackendHealth>("backend_health", { port });
}

export async function apiToken(home?: string): Promise<string> {
  if (!isTauri()) return import.meta.env.VITE_RAD_TOKEN || "";
  return invoke<string>("api_token", { home: home ?? null });
}

export async function defaultHome(): Promise<string> {
  if (!isTauri()) return "";
  return invoke<string>("default_home");
}

export function apiBase(port = 7331): string {
  return import.meta.env.VITE_RAD_API || `http://127.0.0.1:${port}`;
}

/**
 * One full launch-or-reconnect attempt:
 *   locate existing → spawn sidecar if needed → health gate → token → connect.
 * Throws with a user-readable message on any failure (never silent).
 */
export async function launchAndConnect(
  connect: (base: string, token: string) => Promise<void>,
  port = 7331,
): Promise<void> {
  if (!isTauri()) {
    const envTok = import.meta.env.VITE_RAD_TOKEN || "";
    if (!envTok) throw new Error("set VITE_RAD_TOKEN for browser-only mode (no Tauri)");
    await connect(apiBase(port), envTok);
    return;
  }
  let info = await backendInfo();
  // 1 — already managed by this desktop instance?
  if (!info.running) {
    // 2 — something may already be listening (e.g. `rad serve` in a terminal).
    const h = await backendHealth(port).catch(() => null);
    if (!(h && h.ok)) {
      // 3 — start the packaged sidecar (or python fallback in dev).
      try {
        info = await backendStart(port);
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        if (/port_in_use|already in use|10048|98/i.test(msg)) {
          throw new Error(
            `Port ${port} is already in use by another process (possibly a stale RAD backend). ` +
              `Stop it and try again, or run \`rad serve --port ${port + 1}\` and connect manually.`,
          );
        }
        throw new Error(`could not start the RAD backend: ${msg}`);
      }
    }
  }
  // 4 — health gate (waits for the sidecar to bind)
  const h = await backendHealth(port);
  if (!h || !h.ok) {
    throw new Error(
      h?.error
        ? `backend did not become healthy: ${h.error}`
        : "backend health check failed",
    );
  }
  // 5 — token + connect
  const token = await apiToken(info.home || undefined).catch(() => "");
  if (!token) {
    throw new Error(
      "no API token found at <rad home>/api.token — the backend must create it once " +
        "(it is printed by `rad serve` / the sidecar log on first start)",
    );
  }
  await connect(apiBase(port), token);
}

/** Tauri commands for RAD backend lifecycle. Fixed argv only — no user shell. */

export interface BackendInfo {
  running: boolean;
  port: number;
  home: string;
  pid: number | null;
  managed: boolean;
}

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
    return { running: false, port, home: home || "", pid: null, managed: false };
  }
  return invoke<BackendInfo>("backend_start", { port, home: home ?? null });
}

export async function backendStop(): Promise<void> {
  if (!isTauri()) return;
  await invoke("backend_stop");
}

export async function backendInfo(): Promise<BackendInfo> {
  if (!isTauri()) {
    return { running: false, port: 7331, home: "", pid: null, managed: false };
  }
  return invoke<BackendInfo>("backend_info");
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

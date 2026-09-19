/** Typed client for the existing RAD HTTP API. No shell. No tool execution. */

export type Profile = "SAFE" | "STANDARD" | "AUTONOMOUS" | "UNRESTRICTED" | "CUSTOM";

export interface AuthoritySnapshot {
  profile: Profile;
  blurb: string;
  confirmation: string;
  confirmation_is_automatic: boolean;
  unrestricted: boolean;
  unrestricted_authorized: boolean;
  scopes: { workspace_only: boolean; extra_paths: string[]; hosts: string[] };
  capabilities: Record<string, { capability: string; effect: string; granted: boolean }>;
  policy_capabilities: Record<string, string>;
  passthrough: boolean;
  budgets: { tool_calls: number; model_calls: number; retries: number; note: string };
  invariants: Record<string, string | number | boolean>;
  updated: number;
}

export interface Status {
  ok: boolean;
  version: string;
  home?: string;
  workspace?: string;
  auto?: boolean;
  chain?: string[];
  authority?: {
    profile?: Profile;
    confirmation?: string;
    unrestricted?: boolean;
    confirmation_is_automatic?: boolean;
  };
  objectives?: { total: number; by_status: Record<string, number>; open_tasks: number };
}

export interface ObjectiveRow {
  id: string;
  goal: string;
  status: string;
  verification?: string;
  usage?: Record<string, number>;
  budget?: Record<string, number>;
  result?: string;
}

export interface TaskRow {
  id: string;
  title?: string;
  text?: string;
  status: string;
  objective_id?: string;
  goal?: string;
  verification?: { status?: string };
}

export interface Settings {
  workspace: string;
  free_lock: boolean;
  force_provider: string | null;
  model: string | null;
  tts: string;
  stt: string;
  allow_outside_workspace: boolean;
  allow_localhost_web: boolean;
  auto: boolean;
  api_port: number;
  tool_router: string;
  authority: AuthoritySnapshot;
  note: string;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export class RadClient {
  base: string;
  token: string;

  constructor(base: string, token: string) {
    this.base = base.replace(/\/$/, "");
    this.token = token;
  }

  private async req<T>(method: string, path: string, body?: unknown): Promise<T> {
    const headers: Record<string, string> = {
      Authorization: `Bearer ${this.token}`,
    };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    const res = await fetch(`${this.base}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const data = (await res.json().catch(() => ({}))) as { error?: string };
    if (!res.ok) throw new ApiError(res.status, data.error || res.statusText);
    return data as T;
  }

  health() {
    return this.req<{ ok: boolean; version: string }>("GET", "/v1/health");
  }
  status() {
    return this.req<Status>("GET", "/v1/status");
  }
  authority() {
    return this.req<AuthoritySnapshot>("GET", "/v1/authority");
  }
  setAuthority(body: {
    profile: Profile;
    confirm_unrestricted?: boolean;
    capabilities?: Record<string, string>;
    scopes?: Record<string, unknown>;
    confirmation?: string;
  }) {
    return this.req<AuthoritySnapshot>("PUT", "/v1/authority", body);
  }
  settings() {
    return this.req<Settings>("GET", "/v1/settings");
  }
  setSettings(body: Record<string, unknown>) {
    return this.req<Settings>("PUT", "/v1/settings", body);
  }
  chat(text: string) {
    return this.req<{ reply: string; via?: string }>("POST", "/v1/chat", { text });
  }
  objectives(active = false) {
    return this.req<{ objectives: ObjectiveRow[] }>(
      "GET",
      `/v1/objectives${active ? "?active=1" : ""}`,
    );
  }
  createObjective(goal: string, run = true) {
    return this.req<ObjectiveRow & { started?: boolean; note?: string }>(
      "POST",
      "/v1/objectives",
      { goal, run },
    );
  }
  objective(id: string) {
    return this.req<ObjectiveRow & { tasks?: TaskRow[] }>("GET", `/v1/objectives/${id}`);
  }
  trace(id: string) {
    return this.req<{
      objective: ObjectiveRow;
      tasks: TaskRow[];
      verification: Record<string, unknown>;
    }>("GET", `/v1/objectives/${id}/trace`);
  }
  tasks() {
    return this.req<{ tasks: TaskRow[] }>("GET", "/v1/tasks");
  }
  events(n = 80) {
    return this.req<{ events: Array<{ kind: string; at: number; data: Record<string, unknown> }> }>(
      "GET",
      `/v1/events?n=${n}`,
    );
  }
}

export const ROUTES = [
  "/v1/health",
  "/v1/status",
  "/v1/authority",
  "/v1/settings",
  "/v1/chat",
  "/v1/objectives",
  "/v1/tasks",
  "/v1/events",
  "/v1/policy",
  "/v1/audit",
] as const;

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
  verification?: string | { status?: string };
  usage?: Record<string, number>;
  budget?: Record<string, number>;
  result?: string;
  created?: number;
  updated?: number;
  started?: boolean;
  note?: string;
  tasks?: TaskRow[];
}

export interface TaskRow {
  id: string;
  title?: string;
  text?: string;
  status: string;
  objective_id?: string;
  goal?: string;
  depends_on?: string[];
  attempts?: number;
  verification?: { status?: string; evidence?: Array<{ check?: string; ok?: boolean; detail?: string }> };
  current_tool?: string;
}

export interface ObservationRow {
  id: string;
  at?: number;
  tool: string;
  status?: string;
  output?: string;
  args?: Record<string, unknown>;
  task_id?: string;
  evidence?: Array<Record<string, unknown>>;
}

export interface ArtifactRow {
  id: string;
  location: string;
  sha256?: string;
  version?: number;
  size?: number;
  task_id?: string;
  creator?: string;
  type?: string;
}

export interface EventRow {
  seq?: number;
  kind: string;
  at: number;
  task_id?: string;
  objective_id?: string;
  data?: Record<string, unknown>;
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
    return this.req<ObjectiveRow>(
      "POST",
      "/v1/objectives",
      { goal, run },
    );
  }
  objective(id: string) {
    return this.req<ObjectiveRow & { tasks?: TaskRow[] }>("GET", `/v1/objectives/${id}`);
  }
  lifecycle(id: string, action: "pause" | "resume" | "cancel" | "run") {
    return this.req<ObjectiveRow>(
      "POST",
      `/v1/objectives/${id}/${action}`,
      {},
    );
  }
  trace(id: string) {
    return this.req<{
      objective: ObjectiveRow;
      tasks: TaskRow[];
      verification: Record<string, unknown>;
      observations?: ObservationRow[];
      artifacts?: ArtifactRow[];
    }>("GET", `/v1/objectives/${id}/trace`);
  }
  events(id: string, n = 200) {
    return this.req<{ events: EventRow[] }>("GET", `/v1/objectives/${id}/events?n=${n}`);
  }
  globalEvents(n = 80) {
    return this.req<{ events: EventRow[] }>("GET", `/v1/events?n=${n}`);
  }
  why(id: string, q: string) {
    return this.req<Record<string, unknown>>(
      "GET",
      `/v1/objectives/${id}/why?q=${encodeURIComponent(q)}`,
    );
  }
  artifacts(id: string) {
    return this.req<{ artifacts: ArtifactRow[] }>("GET", `/v1/objectives/${id}/artifacts`);
  }
  artifactBody(id: string, artId: string) {
    return this.req<{ path: string; text: string; binary?: boolean; sha256?: string }>(
      "GET",
      `/v1/objectives/${id}/artifacts/${encodeURIComponent(artId)}`,
    );
  }
  usage() {
    return this.req<{
      totals: Record<string, number>;
      per_objective: Array<{ id: string; goal: string; status: string; usage: Record<string, number>; budget: Record<string, number> }>;
      free_lock: boolean;
      note: string;
      remaining_quota_note: string;
    }>("GET", "/v1/usage");
  }
  tasks() {
    return this.req<{ tasks: TaskRow[] }>("GET", "/v1/tasks");
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
  "/v1/usage",
  "/v1/policy",
  "/v1/audit",
] as const;

export function verifyLabel(v: ObjectiveRow["verification"]): string {
  if (!v) return "—";
  if (typeof v === "string") return v || "—";
  return v.status || "—";
}

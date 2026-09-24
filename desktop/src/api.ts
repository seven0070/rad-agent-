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

export const DEFAULT_AUTH_BUDGETS = {
  tool_calls: 60,
  model_calls: 80,
  retries: 6,
  note: "",
};

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
  running_objectives?: string[];
  memory?: Record<string, number>;
  jobs?: number;
  background_routines?: number;
  pending_migrations?: string[];
  last_event?: { kind: string; at: number; seq: number } | null;
}

export interface ObjectiveRow {
  id: string;
  goal: string;
  status: string;
  created: number;
  updated: number;
  verification?: string;
  usage?: Record<string, number>;
  budget?: Record<string, number>;
  result?: string;
  result_summary?: string;
  failure?: string;
  plan_version?: number;
}

export interface TaskRow {
  id: string;
  text?: string;
  title?: string;
  status: string;
  depends_on?: string[];
  checks?: Array<{ kind: string; args?: Record<string, unknown>; description?: string }>;
  objective_id?: string;
  goal?: string;
  attempts?: number;
  max_attempts?: number;
  note?: string;
  failure_class?: string;
  reply?: string;
  started?: number | null;
  finished?: number | null;
  active?: boolean;
  agent?: string;
  plan_version?: number;
  verification?: { status?: string; summary?: string; results?: Array<Record<string, unknown>>; [k: string]: unknown };
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

export interface Artifact {
  id: string;
  objective_id: string;
  task_id: string;
  type: string;
  location: string;
  creator: string;
  sha256: string;
  size: number;
  version: number;
  parent: string | null;
  at: number;
  verification: Record<string, unknown>;
}

export interface ArtifactContent {
  artifact: Artifact;
  path: string;
  sha256: string;
  bytes: number;
  lines: number;
  truncated: boolean;
  preview: string;
}

export interface PlanView {
  objective_id: string;
  plan_version: number;
  source: string;
  attempts: number;
  estimated_tools: number | null;
  compacted: boolean;
  replans: Array<{ plan_version: number; task: string; new_tasks: string[]; superseded: string[]; at: number }>;
  tasks: Array<{ id: string; text: string; depends_on: string[]; checks: string[]; status: string; plan_version: number }>;
}

export interface RecoveryView {
  objective_id: string;
  decisions: Array<{ at: number; task_id: string; task: string; strategy: string; failure_class: string; reason: string }>;
  failed_tasks: Array<{ id: string; text: string; status: string; failure_class: string; note: string; attempts: number }>;
  retries_used: number;
  retry_budget: number;
}

export interface LiveView {
  objective: ObjectiveRow;
  status: string;
  plan_version: number;
  current_task: { id: string; text: string; status: string; started: number | null; attempts: number } | null;
  tasks: { total: number; open: number; by_status: Record<string, number> };
  budget: Record<string, unknown>;
  usage: Record<string, number>;
  artifacts: number;
  retries: { used: number; budget: number };
  verification: string;
  events: RadEvent[];
}

export interface RadEvent {
  kind: string;
  at: number;
  objective_id: string;
  task_id: string;
  data: Record<string, unknown>;
  seq: number;
}

export interface UsageRollup {
  count: number;
  tool_calls: number;
  model_calls: number;
  money_usd: number;
  tokens: number;
  objectives: Array<{ id: string; status: string; goal: string; tool_calls: number; model_calls: number; money_usd: number; tokens: number }>;
  note?: string;
}

export interface MemoryRow {
  id: string;
  layer: string;
  text: string;
  origin: string;
  confidence: number;
  verification: string;
  strength: number;
}

export interface WhyArtifact {
  artifact: Artifact;
  versions: Artifact[];
  action: { id: string; tool: string; args: Record<string, unknown>; status: string; at: number } | null;
  task: { id: string; text: string; attempt: number | null };
  evidence: Array<Record<string, unknown>>;
  verification: Record<string, unknown>;
}

export interface WhyClaim {
  claim: string;
  support: Array<{ score: number; tool: string; source: string; trusted: boolean; excerpt: string }>;
  verdict: "supported" | "weak" | "unsupported";
}

export interface AuditRow {
  at: number;
  tool: string;
  cap: string;
  resource: string;
  effect: string;
  reason: string;
  by: string;
  actor: string;
  outcome: string;
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

  // ---- core
  health() {
    return this.req<{ ok: boolean; version: string; running?: string[] }>("GET", "/v1/health");
  }
  status() {
    return this.req<Status>("GET", "/v1/status");
  }
  authority() {
    return this.req<AuthoritySnapshot>("GET", "/v1/authority");
  }
  ledger<T = any>() {
    return this.req<T>("GET", "/api/ledger");
  }
  vitals<T = any>() {
    return this.req<T>("GET", "/api/vitals");
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
  policy() {
    return this.req<{
      defaults: Record<string, string>;
      rules: Array<{ capability: string; effect: string; match: string; limits: Record<string, unknown>; note: string }>;
      web_allow: string[];
      authority: AuthoritySnapshot;
    }>("GET", "/v1/policy");
  }
  audit(n = 50, effect?: string) {
    return this.req<{ audit: AuditRow[] }>(
      "GET",
      `/v1/audit?n=${n}${effect ? `&effect=${encodeURIComponent(effect)}` : ""}`,
    );
  }
  tools() {
    return this.req<{
      tools: Array<{ name: string; capability: string; policy: string; description: string }>;
    }>("GET", "/v1/tools");
  }

  // ---- objectives
  objectives(active = false) {
    return this.req<{ objectives: ObjectiveRow[] }>(
      "GET",
      `/v1/objectives${active ? "?active=1" : ""}`,
    );
  }
  createObjective(goal: string, run = true, criteria: string[] = [], constraints: string[] = []) {
    return this.req<ObjectiveRow & { started?: boolean; note?: string }>(
      "POST",
      "/v1/objectives",
      { goal, run, criteria, constraints },
    );
  }
  objective(id: string) {
    return this.req<ObjectiveRow & { tasks?: TaskRow[]; success_criteria?: string[]; constraints?: string[] }>(
      "GET",
      `/v1/objectives/${id}`,
    );
  }
  objectiveAction(id: string, action: "resume" | "pause" | "cancel" | "run") {
    return this.req<{ id: string; status: string; started?: boolean; note?: string }>(
      "POST",
      `/v1/objectives/${id}/${action}`,
      {},
    );
  }
  events(objectiveId: string, sinceSeq = 0, n = 500) {
    return this.req<{ events: RadEvent[] }>(
      "GET",
      `/v1/objectives/${objectiveId}/events?since_seq=${sinceSeq}&n=${n}`,
    );
  }
  trace(id: string) {
    return this.req<{
      objective: ObjectiveRow;
      tasks: TaskRow[];
      verification: Record<string, unknown>;
    }>("GET", `/v1/objectives/${id}/trace`);
  }
  plan(id: string) {
    return this.req<PlanView>("GET", `/v1/objectives/${id}/plan`);
  }
  recovery(id: string) {
    return this.req<RecoveryView>("GET", `/v1/objectives/${id}/recovery`);
  }
  live(id: string, sinceSeq = 0, n = 50) {
    return this.req<LiveView>("GET", `/v1/objectives/${id}/live?since_seq=${sinceSeq}&n=${n}`);
  }
  observations(id: string, n = 400) {
    return this.req<{
      objective_id: string;
      count: number;
      observations: Array<{
        id: string;
        task_id: string;
        tool: string;
        args: Record<string, string>;
        status: string;
        duration_ms: number;
        output: string;
        artifacts: string[];
        evidence_kinds: string[];
        at: number;
      }>;
    }>("GET", `/v1/objectives/${id}/observations?n=${n}`);
  }
  artifacts(id: string) {
    return this.req<{ objective_id: string; count: number; artifacts: Artifact[] }>(
      "GET",
      `/v1/objectives/${id}/artifacts`,
    );
  }
  artifactContent(id: string, ref: string) {
    return this.req<ArtifactContent>(
      "GET",
      `/v1/objectives/${id}/artifact-content?ref=${encodeURIComponent(ref)}`,
    );
  }
  why(id: string, q: string) {
    return this.req<WhyArtifact | WhyClaim>("GET", `/v1/objectives/${id}/why?q=${encodeURIComponent(q)}`);
  }
  tasks() {
    return this.req<{ tasks: TaskRow[] }>("GET", "/v1/tasks");
  }
  eventsGlobal(n = 200, kind?: string) {
    return this.req<{ events: RadEvent[]; n: number }>(
      "GET",
      `/v1/events?n=${n}${kind ? `&kind=${encodeURIComponent(kind)}` : ""}`,
    );
  }

  // ---- usage / memory
  usage() {
    return this.req<UsageRollup>("GET", "/v1/usage");
  }
  memory(layer?: string, n = 50) {
    return this.req<{ memories: Record<string, MemoryRow[]> }>(
      "GET",
      `/v1/memory${layer ? `?layer=${layer}` : ""}&n=${n}`,
    );
  }
  recall(q: string, k = 5) {
    return this.req<{ memories: MemoryRow[] }>(
      "GET",
      `/v1/memory/recall?q=${encodeURIComponent(q)}&k=${k}`,
    );
  }
  remember(text: string, layer = "semantic") {
    return this.req<MemoryRow>("POST", "/v1/memory", { text, layer });
  }
  skillsManifest() {
    return this.req<{ skills: any[] }>("GET", "/v1/skills?view=manifest");
  }
  providersHealth() {
    return this.req<{ providers: any[] }>("GET", "/v1/providers/health");
  }
}

export const ROUTES = [
  "/v1/health",
  "/v1/status",
  "/v1/authority",
  "/v1/settings",
  "/v1/chat",
  "/v1/objectives",
  "/v1/objectives/{id}",
  "/v1/objectives/{id}/resume",
  "/v1/objectives/{id}/pause",
  "/v1/objectives/{id}/cancel",
  "/v1/objectives/{id}/run",
  "/v1/objectives/{id}/events",
  "/v1/objectives/{id}/trace",
  "/v1/objectives/{id}/plan",
  "/v1/objectives/{id}/recovery",
  "/v1/objectives/{id}/observations",
  "/v1/objectives/{id}/live",
  "/v1/objectives/{id}/artifacts",
  "/v1/objectives/{id}/artifact-content",
  "/v1/objectives/{id}/why",
  "/v1/tasks",
  "/v1/events",
  "/v1/policy",
  "/v1/audit",
  "/v1/tools",
  "/v1/usage",
  "/v1/memory",
  "/v1/memory/recall",
] as const;

export const SETTINGS_SAFE_KEYS = [
  "workspace",
  "free_lock",
  "force_provider",
  "model",
  "tts",
  "stt",
  "allow_outside_workspace",
  "allow_localhost_web",
] as const;

export type SettingsSafeKey = (typeof SETTINGS_SAFE_KEYS)[number];

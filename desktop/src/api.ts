/** Typed client for the existing RAD HTTP API. No shell. No tool execution. */

export type Profile = "SAFE" | "STANDARD" | "AUTONOMOUS" | "UNRESTRICTED" | "CUSTOM";

export type ObjectiveStatus =
  | "pending"
  | "planning"
  | "running"
  | "paused"
  | "needs_user"
  | "completed"
  | "failed"
  | "cancelled"
  | "expired";

export type MemoryLayer = "episodic" | "semantic" | "procedural";

export interface BudgetFields {
  tool_calls?: number;
  model_calls?: number;
  retries?: number;
  seconds?: number;
  money_usd?: number;
  tokens?: number;
  agents?: number;
}

export interface UsageFields {
  tool_calls: number;
  model_calls: number;
  retries: number;
  seconds: number;
  money_usd: number;
  tokens: number;
  agents: number;
}

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

export interface Health {
  ok: boolean;
  version: string;
  schema: number;
  running: string[];
}

export interface Status {
  ok: boolean;
  version: string;
  schema?: number;
  pending_migrations?: string[];
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
  memory?: Record<string, number>;
  jobs?: number;
  background_routines?: number;
  running_objectives?: string[];
  last_event?: { kind: string; at: number; seq: number };
}

export interface Verification {
  status?: string;
  [key: string]: unknown;
}

export interface ObjectiveRow {
  id: string;
  goal: string;
  status: string;
  created?: number;
  updated?: number;
  verification?: string;
  usage?: Record<string, number>;
  budget?: Record<string, number>;
  result?: string;
}

export interface ObjectiveDetail {
  id: string;
  goal: string;
  status: string;
  created: number;
  updated: number;
  success_criteria: string[];
  constraints: string[];
  priority: string;
  budget: BudgetFields;
  usage: UsageFields;
  deadline: number | null;
  finished: number | null;
  result: string;
  failure: string;
  verification: Verification;
  auto: boolean;
  tags: string[];
  result_summary: string;
  budget_status: Record<string, unknown>;
  plan_version: number;
  tasks?: TaskRow[];
}

export interface TaskRow {
  id: string;
  title?: string;
  text?: string;
  status: string;
  objective_id?: string;
  goal?: string;
  verification?: Verification;
}

export interface RadEvent {
  seq: number;
  kind: string;
  at: number;
  objective_id?: string;
  task_id?: string;
  data?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface MemoryRow {
  id: string;
  layer: MemoryLayer;
  text: string;
  origin: string;
  confidence: number;
  verification?: string;
  strength: number;
}

export interface ToolRow {
  name: string;
  capability: string;
  policy: string;
  description: string;
}

export interface DoctorFinding {
  check: string;
  status: string;
  message: string;
  fixed: boolean;
  detail?: string[];
}

export interface WhySupport {
  score: number;
  tool: string;
  source: string;
  trusted: boolean;
  observation: string;
  task: string;
  at: number;
  excerpt: string;
}

export interface WhyReport {
  claim: string;
  support: WhySupport[];
  verdict: string;
}

export interface ArtifactReport {
  artifact: Record<string, unknown>;
  versions: Array<Record<string, unknown>>;
  action: Record<string, unknown> | null;
  task: { id: string; text: string; attempt?: number | null };
  evidence: Array<Record<string, unknown>>;
  verification: Verification;
}

export interface WorldView {
  matches?: Array<Record<string, unknown>>;
  entities?: Record<string, unknown> | unknown[];
  relations?: Array<Record<string, unknown>>;
  disputes?: Array<Record<string, unknown>>;
  counts?: { entities: number; relations: number };
}

export interface PolicyView {
  defaults: Record<string, string>;
  rules: Array<Record<string, unknown>>;
  web_allow: unknown[];
  authority: AuthoritySnapshot;
}

export interface AgentsView {
  agents: Array<Record<string, unknown>>;
  states: Record<string, unknown>;
  runs: Array<Record<string, unknown>>;
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

export const BUDGET_KEYS = [
  "tool_calls",
  "model_calls",
  "retries",
  "seconds",
  "money_usd",
  "tokens",
  "agents",
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
    return this.req<Health>("GET", "/v1/health");
  }
  status() {
    return this.req<Status>("GET", "/v1/status");
  }
  doctor(fix = false, probe = false) {
    return this.req<{ findings: DoctorFinding[]; fix_applied: boolean }>(
      "GET",
      `/v1/doctor?fix=${fix ? 1 : 0}&probe=${probe ? 1 : 0}`,
    );
  }
  authority() {
    return this.req<AuthoritySnapshot>("GET", "/v1/authority");
  }
  policy() {
    return this.req<PolicyView>("GET", "/v1/policy");
  }
  audit(n = 50) {
    return this.req<Array<Record<string, unknown>>>("GET", `/v1/audit?n=${n}`);
  }
  user() {
    return this.req<Record<string, unknown>>(
      "GET",
      `/v1/user?${new URLSearchParams({ t: String(Date.now()) }).toString()}`,
    );
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
    const safe: Record<string, unknown> = {};
    for (const key of Object.keys(body)) {
      if ((SETTINGS_SAFE_KEYS as readonly string[]).includes(key)) safe[key] = body[key];
    }
    return this.req<Settings>("PUT", "/v1/settings", safe);
  }
  chat(text: string) {
    return this.req<{ reply: string; via?: string }>("POST", "/v1/chat", { text });
  }
  world(q?: string) {
    const params = new URLSearchParams();
    if (q !== undefined) params.set("q", q);
    const qs = params.toString();
    return this.req<WorldView>("GET", `/v1/world${qs ? `?${qs}` : ""}`);
  }
  objectives(active = false) {
    return this.req<{ objectives: ObjectiveRow[] }>(
      "GET",
      `/v1/objectives${active ? "?active=1" : ""}`,
    );
  }
  createObjective(
    goal: string,
    opts: { run?: boolean; criteria?: string[]; constraints?: string[]; budget?: BudgetFields } = {},
  ) {
    const { run, criteria, constraints, budget } = opts;
    if (budget) {
      for (const key of Object.keys(budget)) {
        if (!(BUDGET_KEYS as readonly string[]).includes(key)) {
          throw new TypeError(`unknown budget key "${key}", allowed: ${BUDGET_KEYS.join(", ")}`);
        }
      }
    }
    const body: Record<string, unknown> = { goal };
    if (run !== undefined) body.run = run;
    if (criteria !== undefined) body.criteria = criteria;
    if (constraints !== undefined) body.constraints = constraints;
    if (budget !== undefined) body.budget = budget;
    return this.req<ObjectiveRow & { started?: boolean; note?: string }>("POST", "/v1/objectives", body);
  }
  objective(id: string) {
    return this.req<ObjectiveDetail>("GET", `/v1/objectives/${id}`);
  }
  objectiveEvents(id: string, opts: { kind?: string; sinceSeq?: number; n?: number } = {}) {
    const params = new URLSearchParams();
    if (opts.kind !== undefined) params.set("kind", opts.kind);
    if (opts.sinceSeq !== undefined) params.set("since_seq", String(opts.sinceSeq));
    if (opts.n !== undefined) params.set("n", String(opts.n));
    const qs = params.toString();
    return this.req<{ events: RadEvent[] }>(
      "GET",
      `/v1/objectives/${id}/events${qs ? `?${qs}` : ""}`,
    );
  }
  objectiveAction(id: string, action: "resume" | "pause" | "cancel") {
    if (action === "resume") {
      return this.req<{ id: string; status: "resuming" }>("POST", `/v1/objectives/${id}/resume`);
    }
    return this.req<ObjectiveRow>("POST", `/v1/objectives/${id}/${action}`);
  }
  objectiveWhy(id: string, q: string) {
    return this.req<ArtifactReport | WhyReport>(
      "GET",
      `/v1/objectives/${id}/why?${new URLSearchParams({ q }).toString()}`,
    );
  }
  trace(id: string) {
    return this.req<{
      objective: ObjectiveRow;
      tasks: TaskRow[];
      verification: Verification;
    }>("GET", `/v1/objectives/${id}/trace`);
  }
  tasks() {
    return this.req<{ tasks: TaskRow[] }>("GET", "/v1/tasks");
  }
  tools() {
    return this.req<{ tools: ToolRow[] }>("GET", "/v1/tools");
  }
  memoryRecall(q = "", k = 5) {
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    params.set("k", String(k));
    return this.req<{ memories: MemoryRow[] }>("GET", `/v1/memory/recall?${params.toString()}`);
  }
  memoryAdd(text: string, layer: MemoryLayer = "semantic") {
    return this.req<MemoryRow>("POST", "/v1/memory", { text, layer });
  }
  events(n = 80, opts: { kind?: string; objective?: string } = {}) {
    const params = new URLSearchParams();
    params.set("n", String(n));
    if (opts.kind !== undefined) params.set("kind", opts.kind);
    if (opts.objective !== undefined) params.set("objective", opts.objective);
    return this.req<{ events: RadEvent[]; n: number; stream: string }>(
      "GET",
      `/v1/events?${params.toString()}`,
    );
  }
  benchmarks() {
    return this.req<Record<string, unknown>>("GET", "/v1/benchmarks");
  }
  labHistory(n = 20) {
    return this.req<{ runs: Array<Record<string, unknown>> }>("GET", `/v1/lab/history?n=${n}`);
  }
  evolveCandidates(n = 20) {
    return this.req<{ candidates: Array<Record<string, unknown>> }>(
      "GET",
      `/v1/evolve/candidates?n=${n}`,
    );
  }
  agents() {
    return this.req<AgentsView>("GET", "/v1/agents");
  }
}

export const ROUTES = [
  "/v1/health",
  "/v1/status",
  "/v1/doctor",
  "/v1/authority",
  "/v1/policy",
  "/v1/audit",
  "/v1/user",
  "/v1/settings",
  "/v1/chat",
  "/v1/world",
  "/v1/objectives",
  "/v1/objectives/{id}",
  "/v1/objectives/{id}/resume",
  "/v1/objectives/{id}/pause",
  "/v1/objectives/{id}/cancel",
  "/v1/objectives/{id}/events",
  "/v1/objectives/{id}/trace",
  "/v1/objectives/{id}/why",
  "/v1/memory",
  "/v1/memory/recall",
  "/v1/tasks",
  "/v1/events",
  "/v1/tools",
  "/v1/benchmarks",
  "/v1/lab/history",
  "/v1/evolve/candidates",
  "/v1/agents",
] as const;
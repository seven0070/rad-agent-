/** Display helpers. The backend already redacts secrets at run_tool; this is a
 *  defense-in-depth pass so nothing sensitive is ever rendered, even if a future
 *  endpoint forgets to redact. */

const SECRET_PATTERNS: Array<[RegExp, string]> = [
  [/\b(sk-[A-Za-z0-9_-]{16,})/g, "sk-…REDACTED"],
  [/\b(gh[pousr]_[A-Za-z0-9]{20,})/g, "gh…REDACTED"],
  [/\b(AKIA[0-9A-Z]{16})\b/g, "AKIA…REDACTED"],
  [/\b(xox[baprs]-[A-Za-z0-9-]{10,})/g, "xox…REDACTED"],
  [/\b(api[_-]?key|secret|token|password|passwd|API[_-]?KEY|SECRET|TOKEN|PASSWORD|PASSWD)(\s*[:=]\s*)(['"]?)([^\s'"]{8,})/g, "REDACTED-VALUE"],
  [/-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g, "[PRIVATE KEY REDACTED]"],
  [/(Authorization:\s*Bearer\s+)[A-Za-z0-9._-]{10,}/g, "$1REDACTED"],
];

export function redactText(text: string): string {
  if (!text) return text;
  let out = text;
  for (const [re, rep] of SECRET_PATTERNS) {
    out = rep === "REDACTED-VALUE"
      ? out.replace(re, (_m: string, a: string, b: string, c: string) => `${a}${b}${c}REDACTED`)
      : out.replace(re, rep);
  }
  return out;
}

export function fmtTime(at: number): string {
  if (!at) return "—";
  const d = new Date(at * 1000);
  return d.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function fmtAgo(at: number): string {
  if (!at) return "—";
  const s = Math.max(0, Math.floor(Date.now() / 1000 - at));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export function fmtElapsed(seconds: number): string {
  if (!isFinite(seconds) || seconds < 0) return "—";
  const s = Math.floor(seconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = s % 60;
  if (h) return `${h}h ${m}m ${r}s`;
  if (m) return `${m}m ${r}s`;
  return `${r}s`;
}

export function fmtBytes(n: number): string {
  if (!n) return "0 B";
  const u = ["B", "KB", "MB", "GB"];
  let i = 0;
  let v = n;
  while (v >= 1024 && i < u.length - 1) {
    v /= 1024;
    i++;
  }
  return `${v.toFixed(v >= 100 ? 0 : 1)} ${u[i]}`;
}

export function shortHash(h: string, n = 10): string {
  return h ? h.slice(0, n) + (h.length > n ? "…" : "") : "—";
}

export const TASK_STATES = [
  "PENDING", "READY", "RUNNING", "OBSERVING", "VERIFYING",
  "COMPLETED", "FAILED", "RETRYING", "BLOCKED", "NEEDS_USER", "CANCELLED",
] as const;

export type TaskState = (typeof TASK_STATES)[number];

export function taskStateClass(s: string): string {
  switch (s) {
    case "PENDING": return "ts-pending";
    case "READY": return "ts-ready";
    case "RUNNING": return "ts-running";
    case "OBSERVING": return "ts-observing";
    case "VERIFYING": return "ts-verifying";
    case "COMPLETED": return "ts-completed";
    case "FAILED": return "ts-failed";
    case "RETRYING": return "ts-retrying";
    case "BLOCKED": return "ts-blocked";
    case "NEEDS_USER": return "ts-needs-user";
    case "CANCELLED": return "ts-cancelled";
    default: return "ts-pending";
  }
}

export function objStatusClass(s: string): string {
  const k = (s || "").toLowerCase();
  if (k === "completed") return "os-completed";
  if (k === "failed") return "os-failed";
  if (k === "needs_user") return "os-needs-user";
  if (k === "paused") return "os-paused";
  if (k === "cancelled" || k === "expired") return "os-cancelled";
  return "os-running";
}

export function isActiveObjective(s: string): boolean {
  const k = (s || "").toLowerCase();
  return ["pending", "planning", "running", "paused", "needs_user"].includes(k);
}

/** Pick the objective a live view should follow: newest active, else newest overall. */
export function pickFocus<T extends { id: string; status: string; created: number }>(rows: T[]): T | null {
  if (!rows.length) return null;
  const active = rows.filter((r) => isActiveObjective(r.status));
  const pool = active.length ? active : rows;
  return [...pool].sort((a, b) => b.created - a.created)[0];
}

export function budgetPct(used: number, total: number): number {
  if (!total) return 0;
  return Math.min(100, Math.round((used / total) * 100));
}

import { useEffect, useState } from "react";
import { ArtifactReport, RadClient, WhyReport } from "../api";
import { usePolling } from "../hooks/usePolling";
import { VerificationCard } from "./VerificationCard";

/** Statuses where background polling should stop; the user acts via buttons. */
export const TERMINAL_STATUSES = new Set([
  "completed",
  "failed",
  "cancelled",
  "paused",
  "expired",
  "needs_user",
]);

export function fmtTime(t?: number | null) {
  if (!t) return "—";
  const ms = t < 1e12 ? t * 1000 : t;
  return new Date(ms).toLocaleTimeString();
}

export function fmtAt(t?: number | null) {
  if (!t) return "—";
  const ms = t < 1e12 ? t * 1000 : t;
  return `${new Date(ms).toLocaleDateString()} ${new Date(ms).toLocaleTimeString()}`;
}

function chipClass(v: string | undefined | null) {
  return `chip ${(v || "pending").toLowerCase()}`;
}

/**
 * Full per-objective detail: status + actions, criteria/constraints, budget &
 * usage, result, tasks, events, and the "why" panel. Polling freezes on
 * terminal statuses; resume/pause/cancel go straight through the control plane.
 */
export function ObjectiveDetail({
  client,
  id,
  onBack,
  onOpenObjective,
}: {
  client: RadClient;
  id: string;
  onBack?: () => void;
  onOpenObjective?: (id: string) => void;
}) {
  const [frozen, setFrozen] = useState(false);

  const poll = usePolling(() => client.objective(id), {
    intervalMs: 3000,
    isActive: !!id && !frozen,
  });
  const eventsPoll = usePolling(() => client.objectiveEvents(id, { n: 60 }), {
    intervalMs: 4000,
    isActive: !!id && !frozen,
  });

  useEffect(() => {
    const st = poll.data?.status;
    if (st) setFrozen(TERMINAL_STATUSES.has(st));
  }, [poll.data]);

  const [acting, setActing] = useState("");
  const [actionErr, setActionErr] = useState("");
  const [actionOk, setActionOk] = useState("");

  const act = async (a: "resume" | "pause" | "cancel") => {
    if (acting) return;
    setActing(a);
    setActionErr("");
    setActionOk("");
    try {
      const r = await client.objectiveAction(id, a);
      setActionOk(a === "resume" ? `resuming ${r.id}` : `queued ${a} ${r.id}`);
      await poll.refresh();
    } catch (e) {
      setActionErr(e instanceof Error ? e.message : String(e));
    } finally {
      setActing("");
    }
  };

  const [whyQ, setWhyQ] = useState("");
  const [whyBusy, setWhyBusy] = useState(false);
  const [whyReport, setWhyReport] = useState<WhyReport | ArtifactReport | null>(null);
  const [whyErr, setWhyErr] = useState("");

  const askWhy = async () => {
    const q = whyQ.trim();
    if (!q || whyBusy) return;
    setWhyBusy(true);
    setWhyErr("");
    try {
      setWhyReport(await client.objectiveWhy(id, q));
    } catch (e) {
      setWhyErr(e instanceof Error ? e.message : String(e));
    } finally {
      setWhyBusy(false);
    }
  };

  if (!id) return <p className="lead">Select an objective.</p>;

  const detail = poll.data;
  if (!detail) {
    return (
      <div>
        <h1>Objective</h1>
        <p className="lead">{poll.error || "Loading objective…"}</p>
      </div>
    );
  }

  const events = eventsPoll.data?.events || [];
  const tasks = detail.tasks || [];
  const status = detail.status;
  const canPause = status === "planning" || status === "running" || status === "pending";
  const canResume = status === "paused" || status === "needs_user" || status === "expired";
  const canCancel = status !== "completed" && status !== "cancelled" && status !== "failed";

  const budgetParts =
    Object.entries(detail.budget)
      .filter(([, v]) => v !== undefined)
      .map(([k, v]) => `${k}=${v}`)
      .join(" · ") || "unset";
  const usageParts = Object.entries(detail.usage)
    .map(([k, v]) => `${k}=${v}`)
    .join(" · ");

  return (
    <div>
      <div className="row" style={{ justifyContent: "space-between", marginBottom: 6 }}>
        <h1 style={{ margin: 0 }}>{detail.goal}</h1>
        {onBack && (
          <button className="btn ghost" onClick={onBack}>
            ← Objectives
          </button>
        )}
      </div>
      <div className="row" style={{ marginBottom: 14 }}>
        <span className={chipClass(status)}>{status}</span>
        <span className="meta mono">{detail.id}</span>
        <span className="meta">
          {detail.priority} · auto={String(detail.auto)} · plan v{detail.plan_version}
        </span>
      </div>
      {poll.error && <p className="err">{poll.error}</p>}

      <div className="card">
        <h3>Actions</h3>
        <div className="row">
          {canResume && (
            <button className="btn" disabled={!!acting} onClick={() => void act("resume")}>
              {acting === "resume" ? "Resuming…" : "Resume"}
            </button>
          )}
          {canPause && (
            <button className="btn ghost" disabled={!!acting} onClick={() => void act("pause")}>
              {acting === "pause" ? "Pausing…" : "Pause"}
            </button>
          )}
          {canCancel && (
            <button className="btn warn" disabled={!!acting} onClick={() => void act("cancel")}>
              {acting === "cancel" ? "Cancelling…" : "Cancel"}
            </button>
          )}
          <span className="meta">
            {frozen ? "polling paused — control-plane status is final until you act" : "live polling active"}
          </span>
        </div>
        {actionErr && <p className="err" style={{ marginTop: 8 }}>{actionErr}</p>}
        {actionOk && <p className="ok" style={{ marginTop: 8 }}>{actionOk}</p>}
      </div>

      {detail.success_criteria.length > 0 && (
        <div className="card">
          <h3>Success criteria</h3>
          <ul>
            {detail.success_criteria.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
          {detail.constraints.length > 0 && (
            <>
              <h3>Constraints</h3>
              <ul>
                {detail.constraints.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      <div className="card">
        <h3>Budget &amp; usage</h3>
        <div className="kv">
          <div className="kv-row">
            <span className="k">budget</span>
            <span className="v mono">{budgetParts}</span>
          </div>
          <div className="kv-row">
            <span className="k">usage</span>
            <span className="v mono">{usageParts}</span>
          </div>
          <div className="kv-row">
            <span className="k">budget status</span>
            <span className="v">
              {typeof detail.budget_status.overall === "string"
                ? detail.budget_status.overall
                : JSON.stringify(detail.budget_status)}
            </span>
          </div>
          <div className="kv-row">
            <span className="k">created</span>
            <span className="v">{fmtAt(detail.created)}</span>
          </div>
          <div className="kv-row">
            <span className="k">updated</span>
            <span className="v">{fmtAt(detail.updated)}</span>
          </div>
          {detail.finished ? (
            <div className="kv-row">
              <span className="k">finished</span>
              <span className="v">{fmtAt(detail.finished)}</span>
            </div>
          ) : null}
          {detail.deadline ? (
            <div className="kv-row">
              <span className="k">deadline</span>
              <span className="v">{fmtAt(detail.deadline)}</span>
            </div>
          ) : null}
        </div>
      </div>

      {detail.result_summary && <p className="meta">{detail.result_summary}</p>}
      {detail.result && (
        <div className="card">
          <h3>Result</h3>
          <p className="mono" style={{ whiteSpace: "pre-wrap" }}>{detail.result}</p>
        </div>
      )}
      {detail.failure && (
        <div className="card">
          <h3>Failure</h3>
          <p className="err">{detail.failure}</p>
        </div>
      )}

      <VerificationCard verification={detail.verification} />

      <div className="card">
        <h3>Tasks ({tasks.length})</h3>
        {tasks.length === 0 && <p className="meta">no tasks yet</p>}
        {tasks.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>status</th>
                <th>verified</th>
                <th>task</th>
                <th>objective</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id}>
                  <td>{t.status}</td>
                  <td>{t.verification?.status || "—"}</td>
                  <td>{t.title || t.text || t.id}</td>
                  <td>
                    {t.objective_id && t.objective_id !== id && onOpenObjective ? (
                      <button
                        className="btn ghost"
                        style={{ padding: "1px 6px", fontSize: 11 }}
                        onClick={() => onOpenObjective(t.objective_id!)}
                      >
                        {t.objective_id.slice(0, 8)}
                      </button>
                    ) : (
                      <span className="meta">{t.objective_id || "—"}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h3>Events</h3>
        {events.length === 0 && <p className="meta">{eventsPoll.error || "no events yet"}</p>}
        {events.length > 0 && (
          <div className="events">
            {events.map((e) => (
              <div key={e.seq} className="event">
                <span className="seq">{e.seq}</span>
                <span className="at">{fmtTime(e.at)}</span>
                <span className="kind">{e.kind}</span>
                {e.data ? <span className="data">{JSON.stringify(e.data)}</span> : null}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h3>Why?</h3>
        <div className="row">
          <input
            value={whyQ}
            onChange={(e) => setWhyQ(e.target.value)}
            placeholder="claim or artifact path…"
            style={{ flex: 1, minWidth: 200 }}
            onKeyDown={(e) => {
              if (e.key === "Enter") void askWhy();
            }}
          />
          <button className="btn" disabled={whyBusy} onClick={() => void askWhy()}>
            Why
          </button>
        </div>
        {whyErr && <p className="err" style={{ marginTop: 8 }}>{whyErr}</p>}
        {whyReport && (
          <div style={{ marginTop: 10 }}>
            {"claim" in whyReport ? (
              <WhyReportView report={whyReport} />
            ) : (
              <ArtifactReportView report={whyReport} />
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function WhyReportView({ report }: { report: WhyReport }) {
  return (
    <div>
      <p className="lead">{report.claim}</p>
      <span className={chipClass(report.verdict)}>{report.verdict}</span>
      {report.support.length === 0 && <p className="meta">no supporting evidence</p>}
      {report.support.map((s, i) => (
        <div key={i} className="check" style={{ marginTop: 8 }}>
          <div style={{ flex: 1 }}>
            <div className="verdict">
              score {s.score} · {s.tool} · {s.source} {s.trusted ? "· trusted" : "· untrusted"}
            </div>
            <div className="meta">
              task: {s.task} · {fmtAt(s.at)}
            </div>
            {s.observation && <div className="meta">{s.observation}</div>}
            {s.excerpt && <pre className="trace-pre">{s.excerpt}</pre>}
          </div>
        </div>
      ))}
    </div>
  );
}

function ArtifactReportView({ report }: { report: ArtifactReport }) {
  return (
    <div>
      <div className="kv">
        {Object.entries(report.artifact).map(([k, v]) => (
          <div key={k} className="kv-row">
            <span className="k">{k}</span>
            <span className="v mono">
              {typeof v === "object" && v !== null ? JSON.stringify(v) : String(v)}
            </span>
          </div>
        ))}
      </div>
      {report.versions.length > 0 && (
        <>
          <h3>Versions</h3>
          <pre className="trace-pre">{JSON.stringify(report.versions, null, 2)}</pre>
        </>
      )}
      {report.evidence.length > 0 && (
        <>
          <h3>Evidence</h3>
          {report.evidence.map((e, i) => (
            <pre key={i} className="trace-pre">
              {JSON.stringify(e, null, 2)}
            </pre>
          ))}
        </>
      )}
      <VerificationCard verification={report.verification} />
    </div>
  );
}
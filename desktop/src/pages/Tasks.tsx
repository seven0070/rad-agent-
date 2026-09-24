/** Live task graph. Layout is display-only math over backend tasks; the
 *  controller's ready-set stays authoritative. */
import { useEffect, useMemo, useState } from "react";
import { TaskRow } from "../api";
import { useRad } from "../ctx";
import { layoutTasks } from "../graph";
import { TASK_STATES, fmtTime, redactText, taskStateClass } from "../util";

export default function Tasks() {
  const { client, selected } = useRad();
  const [tasks, setTasks] = useState<TaskRow[]>([]);
  const [detail, setDetail] = useState<TaskRow | null>(null);
  const [err, setErr] = useState("");
  const id = selected?.id;

  useEffect(() => {
    if (!id) {
      setTasks([]);
      setDetail(null);
      return;
    }
    let stop = false;
    const tick = async () => {
      try {
        const o = await client.objective(id);
        if (stop) return;
        const ts = o.tasks || [];
        setTasks(ts);
        setDetail((d) => (d ? (ts.find((t) => t.id === d.id) || d) : d));
        setErr("");
      } catch (e) {
        if (!stop) setErr(String(e));
      }
    };
    void tick();
    const t = setInterval(tick, 2500);
    return () => {
      stop = true;
      clearInterval(t);
    };
  }, [client, id]);

  const g = useMemo(() => layoutTasks(tasks), [tasks]);
  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const t of tasks) c[t.status] = (c[t.status] || 0) + 1;
    return c;
  }, [tasks]);

  if (!id) {
    return (
      <div>
        <h1>Tasks</h1>
        <p className="lead">Select an objective (Objectives tab) to inspect its task graph.</p>
      </div>
    );
  }

  return (
    <div>
      <h1>Task Graph</h1>
      <p className="lead">
        Backend task dependencies for {id}. The frontend does not schedule — the controller
        chooses the ready set.
      </p>
      <div className="row mb-12">
        {TASK_STATES.filter((s) => counts[s]).map((s) => (
          <span key={s} className={`badge ${taskStateClass(s)}`}>
            {s} {counts[s]}
          </span>
        ))}
      </div>
      {err && <p className="err">{err}</p>}
      {tasks.length === 0 && <p className="lead">no tasks yet (objective not planned)</p>}

      <div className="row graph-row">
        <div className="card graph-card">
          <svg width={g.width} height={g.height} viewBox={`0 0 ${g.width} ${g.height}`}>
            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#4a5670" />
              </marker>
            </defs>
            {g.edges.map((e, i) => {
              const a = g.nodes.find((n) => n.id === e.from);
              const b = g.nodes.find((n) => n.id === e.to);
              if (!a || !b) return null;
              const x1 = a.x + a.w;
              const y1 = a.y + a.h / 2;
              const x2 = b.x;
              const y2 = b.y + b.h / 2;
              const mx = (x1 + x2) / 2;
              return (
                <path
                  key={i}
                  d={`M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2 - 4} ${y2}`}
                  fill="none"
                  stroke="#4a5670"
                  strokeWidth={1.4}
                  markerEnd="url(#arrow)"
                />
              );
            })}
            {g.nodes.map((n) => (
              <g key={n.id} onClick={() => setDetail(n.task)} className="cursor-pointer">
                <rect
                  x={n.x}
                  y={n.y}
                  width={n.w}
                  height={n.h}
                  rx={9}
                  className={`node ${taskStateClass(n.task.status)}`}
                />
                <text x={n.x + 10} y={n.y + 20} className="node-title">
                  {(n.task.text || n.task.id).slice(0, 24)}
                </text>
                <text x={n.x + 10} y={n.y + 38} className="node-sub">
                  {n.task.status}
                  {(n.task.attempts ?? 0) > 1 ? ` · try ${n.task.attempts}` : ""}
                </text>
                <text x={n.x + 10} y={n.y + 50} className="node-sub">
                  {n.task.id}
                </text>
              </g>
            ))}
          </svg>
        </div>
        {detail && (
          <div className="card detail-card">
            <div className="row justify-between">
              <b>{detail.id}</b>
              <span className={`badge ${taskStateClass(detail.status)}`}>{detail.status}</span>
            </div>
            <div className="mt-8 fs-13 pre-wrap">{redactText(detail.text || "")}</div>
            <div className="hint mt-8">
              attempts {detail.attempts ?? 0}/{detail.max_attempts ?? 3}
              {detail.agent ? ` · agent ${detail.agent}` : ""}
              {detail.started ? ` · started ${fmtTime(detail.started)}` : ""}
              {detail.finished ? ` · finished ${fmtTime(detail.finished)}` : ""}
            </div>
            {detail.depends_on && detail.depends_on.length > 0 && (
              <div className="hint mt-6">depends on: {detail.depends_on.join(", ")}</div>
            )}
            {(detail.checks || []).length > 0 && (
              <div className="mt-8">
                <label>Machine checks</label>
                {(detail.checks || []).map((c, i) => (
                  <div key={i} className="hint">
                    {c.description || `${c.kind} ${JSON.stringify(c.args || {})}`}
                  </div>
                ))}
              </div>
            )}
            {detail.verification?.status && (
              <div className="mt-8">
                <label>Verification</label>
                <span
                  className={`badge ${
                    detail.verification.status === "VERIFIED" ? "b-ok" : detail.verification.status === "FAILED" ? "b-bad" : "b-warn"
                  }`}
                >
                  {detail.verification.status}
                </span>
                {detail.verification.summary && (
                  <div className="hint mt-4">
                    {redactText(String(detail.verification.summary)).slice(0, 400)}
                  </div>
                )}
              </div>
            )}
            {detail.note && (
              <div className="hint mt-8">
                note: {redactText(detail.note)}
              </div>
            )}
            {detail.failure_class && <div className="hint mt-4">failure class: {detail.failure_class}</div>}
            {(detail.reply || "") && (
              <details className="mt-8">
                <summary className="hint">model reply (redacted)</summary>
                <pre className="reply-pre">{redactText(detail.reply || "").slice(0, 3000)}</pre>
              </details>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

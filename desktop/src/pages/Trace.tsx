/** Tool trace. Reconstructs, per task:
 *  objective → task → authority → policy decision → tool → args → execution →
 *  observation → artifact → verification, from recorded events + observations.
 *  Output is redacted (backend already redacts at run_tool; redacted again here). */
import { useEffect, useMemo, useState } from "react";
import { RadEvent, TaskRow } from "../api";
import { useRad } from "../ctx";
import { fmtTime, redactText, taskStateClass } from "../util";

interface ToolRow {
  at: number;
  action: string;
  taskId: string;
  tool: string;
  cap: string;
  args: Record<string, unknown>;
  status: string;
  policy: string;
  actor: string;
  ms: number;
  observation?: string;
  artifacts: string[];
  output: string;
  refused: boolean;
}

interface TaskTrace {
  task: TaskRow;
  tools: ToolRow[];
  verification: string;
  verificationSummary: string;
}

export default function Trace() {
  const { client, selected, auth } = useRad();
  const [events, setEvents] = useState<RadEvent[]>([]);
  const [tasks, setTasks] = useState<TaskRow[]>([]);
  const [obs, setObs] = useState<Record<string, { output: string; status: string; artifacts: string[] }>>({});
  const [err, setErr] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const id = selected?.id;

  useEffect(() => {
    if (!id) return;
    let stop = false;
    const tick = async () => {
      try {
        const [o, ev, ob] = await Promise.all([
          client.objective(id),
          client.events(id, 0, 2000),
          client.observations(id, 600),
        ]);
        if (stop) return;
        setTasks(o.tasks || []);
        setEvents(ev.events);
        const m: Record<string, { output: string; status: string; artifacts: string[] }> = {};
        for (const r of ob.observations) m[r.id] = { output: r.output, status: r.status, artifacts: r.artifacts };
        setObs(m);
        setErr("");
      } catch (e) {
        if (!stop) setErr(String(e));
      }
    };
    void tick();
    const t = setInterval(tick, 4000);
    return () => {
      stop = true;
      clearInterval(t);
    };
  }, [client, id]);

  const traces = useMemo<TaskTrace[]>(() => buildTraces(tasks, events, obs), [tasks, events, obs]);

  if (!id) {
    return (
      <div>
        <h1>Trace</h1>
        <p className="lead">Select an objective to inspect its execution trace.</p>
      </div>
    );
  }

  return (
    <div>
      <h1>Tool Trace</h1>
      <p className="lead">
        Recorded, redacted execution for {id}. Authority profile:{" "}
        <span className={`pill ${auth.profile}`}>{auth.profile}</span>. No API keys, credentials
        or secrets are exposed.
      </p>
      {err && <p className="err">{err}</p>}
      {traces.length === 0 && !err && <p className="lead">no tasks recorded yet</p>}

      {traces.map((tt) => (
        <div key={tt.task.id} className="card">
          <div
            className="row"
            style={{ justifyContent: "space-between", cursor: "pointer" }}
            onClick={() => setExpanded(expanded === tt.task.id ? null : tt.task.id)}
          >
            <div className="row">
              <span className={`badge ${taskStateClass(tt.task.status)}`}>{tt.task.status}</span>
              <b>{redactText((tt.task.text || tt.task.id).slice(0, 80))}</b>
            </div>
            <div className="row">
              {tt.verification && (
                <span
                  className={`badge ${
                    tt.verification === "VERIFIED" ? "b-ok" : tt.verification === "FAILED" ? "b-bad" : "b-warn"
                  }`}
                >
                  {tt.verification}
                </span>
              )}
              <span className="hint">{tt.tools.length} tool call(s)</span>
            </div>
          </div>
          {expanded === tt.task.id && (
            <div style={{ marginTop: 10 }}>
              {tt.tools.length === 0 && <div className="hint">no tool calls recorded for this task</div>}
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>time</th>
                      <th>tool</th>
                      <th>capability</th>
                      <th>policy</th>
                      <th>args</th>
                      <th>result</th>
                      <th>ms</th>
                      <th>artifact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tt.tools.map((r, i) => (
                      <tr key={i}>
                        <td className="hint">{fmtTime(r.at)}</td>
                        <td>{r.tool}</td>
                        <td className="hint">{r.cap || "—"}</td>
                        <td>
                          <span
                            className={`badge ${
                              ["ALLOW", "UNVERIFIED"].includes(r.policy) ? "b-ok"
                                : ["DENY", "HARD_DENY", "SCOPE_VIOLATION", "UNAUTHORIZED"].includes(r.policy) ? "b-bad"
                                : "b-warn"
                            }`}
                          >
                            {r.policy || (r.refused ? "refused" : "—")}
                          </span>
                        </td>
                        <td className="hint" title={redactText(JSON.stringify(r.args))}>
                          {redactText(JSON.stringify(r.args)).slice(0, 60)}
                        </td>
                        <td>
                          <span className={`badge ${r.status === "success" ? "b-ok" : "b-bad"}`}>{r.status}</span>
                        </td>
                        <td className="hint">{r.ms}</td>
                        <td className="hint" title={(r.artifacts || []).join("\n")}>
                          {(r.artifacts || []).map((a) => (a.split("/").pop() || a)).slice(0, 2).join(", ") || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {tt.tools.some((r) => r.output) && (
                <details style={{ marginTop: 8 }}>
                  <summary className="hint">output summary (redacted)</summary>
                  {tt.tools.filter((r) => r.output).map((r, i) => (
                    <div key={i} className="obs-out">
                      <span className="hint">
                        {r.tool} → {redactText(r.output).slice(0, 400)}
                      </span>
                    </div>
                  ))}
                </details>
              )}
              {tt.verificationSummary && (
                <div className="hint" style={{ marginTop: 8 }}>
                  verification: {redactText(tt.verificationSummary)}
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function buildTraces(
  tasks: TaskRow[],
  events: RadEvent[],
  obs: Record<string, { output: string; status: string; artifacts: string[] }>,
): TaskTrace[] {
  // index tool events by task + action
  const byAction = new Map<string, { called?: RadEvent; result?: RadEvent }>();
  for (const e of events) {
    if (e.kind === "TOOL_CALLED" || e.kind === "TOOL_RESULT") {
      const action = String(e.data.action || "");
      if (!action) continue;
      const slot = byAction.get(action) || {};
      if (e.kind === "TOOL_CALLED") slot.called = e;
      else slot.result = e;
      byAction.set(action, slot);
    }
  }
  const out: TaskTrace[] = tasks.map((t) => {
    const rows: ToolRow[] = [];
    for (const e of events) {
      if (e.task_id !== t.id) continue;
      if (e.kind !== "TOOL_CALLED" && e.kind !== "TOOL_RESULT") continue;
      const action = String(e.data.action || "");
      const slot = byAction.get(action) || {};
      const ref = e.kind === "TOOL_RESULT" ? e : slot.result;
      const call = e.kind === "TOOL_CALLED" ? e : slot.called;
      const obsRec = ref?.data.observation ? obs[String(ref.data.observation)] : undefined;
      const refused =
        ref?.data.policy === "DENY" ||
        ref?.data.policy === "HARD_DENY" ||
        ref?.data.policy === "SCOPE_VIOLATION" ||
        ref?.data.policy === "UNAUTHORIZED" ||
        (obsRec?.status === "blocked" || obsRec?.status === "declined");
      rows.push({
        at: (e.kind === "TOOL_RESULT" ? ref?.at ?? e.at : e.at),
        action,
        taskId: t.id,
        tool: String(ref?.data.tool ?? call?.data.tool ?? "—"),
        cap: String(ref?.data.cap ?? call?.data.cap ?? ""),
        args: (call?.data.args as Record<string, unknown>) || {},
        status: String(ref?.data.status ?? obsRec?.status ?? "—"),
        policy: String(ref?.data.policy ?? ""),
        actor: String(call?.data.actor ?? ""),
        ms: Number(ref?.data.ms ?? 0),
        observation: obsRec ? String(ref!.data.observation) : undefined,
        artifacts: obsRec?.artifacts || (ref?.data.artifacts as string[]) || [],
        output: obsRec?.output || "",
        refused,
      });
    }
    rows.sort((a, b) => a.at - b.at);
    // one row per action: TOOL_CALLED + TOOL_RESULT of the same call collapse
    const seen = new Set<string>();
    const dedup = rows.filter((r) => {
      const k = r.action || `${r.at}-${r.tool}`;
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    });
    return {
      task: t,
      tools: dedup,
      verification: t.verification?.status || "",
      verificationSummary: String(t.verification?.summary || ""),
    };
  });
  return out;
}

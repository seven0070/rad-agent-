/** Objective dashboard. Every column is persisted backend state; actions only
 *  call endpoints the backend actually supports for that state. */
import { useCallback, useEffect, useState } from "react";
import { ApiError, ObjectiveRow } from "../api";
import { useRad } from "../ctx";
import { fmtAgo, fmtTime, objStatusClass } from "../util";

export default function Objectives() {
  const { client, selected, select, auth, refresh } = useRad();
  const [rows, setRows] = useState<ObjectiveRow[]>([]);
  const [activeOnly, setActiveOnly] = useState(false);
  const [goal, setGoal] = useState("");
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const [creating, setCreating] = useState(false);
  const [acting, setActing] = useState<{ id: string; action: string } | null>(null);

  const load = useCallback(async () => {
    const r = await client.objectives(activeOnly);
    setRows(r.objectives);
  }, [client, activeOnly]);

  useEffect(() => {
    void load().catch((e) => setErr(String(e)));
    const t = setInterval(() => void load().catch(() => {}), 5000);
    return () => clearInterval(t);
  }, [load]);

  const create = async () => {
    const g = goal.trim();
    if (!g || creating) return;
    setCreating(true);
    setErr("");
    setOk("");
    try {
      const o = await client.createObjective(g, true);
      setGoal("");
      select(o.id);
      setOk(o.started ? `${o.id} started` : `${o.id} created PENDING${o.note ? " — " + o.note : ""}`);
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  };

  const act = async (id: string, action: "run" | "resume" | "pause" | "cancel") => {
    if (acting) return;
    setActing({ id, action });
    setErr("");
    setOk("");
    try {
      const r = await client.objectiveAction(id, action);
      setOk(`${id.slice(0, 8)}: ${action} → ${r.status}`);
      await load();
      await refresh();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    } finally {
      setActing(null);
    }
  };

  return (
    <div>
      <h1>Objectives</h1>
      <p className="lead">
        Existing control plane. Desktop displays and operates objectives — it is not a React
        task engine. Authority at run time: <span className={`pill ${auth.profile}`}>{auth.profile}</span>
      </p>

      <div className="card">
        <label>New objective</label>
        <div className="row">
          <input value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="goal" />
          <button className="btn" disabled={creating || !goal.trim()} onClick={() => void create()}>
            {creating ? "Creating…" : "Create"}
          </button>
        </div>
        {err && <p className="err">{err}</p>}
        {ok && <p className="ok">{ok}</p>}
      </div>

      <div className="card">
        <div className="row" style={{ marginBottom: 10 }}>
          <label style={{ marginBottom: 0 }}>
            <input
              type="checkbox"
              checked={activeOnly}
              onChange={(e) => setActiveOnly(e.target.checked)}
              style={{ width: "auto", marginRight: 6 }}
            />
            active only
          </label>
          <span className="hint">{rows.length} shown · authority profile {auth.profile}</span>
          <button className="btn ghost" style={{ marginLeft: "auto", padding: "3px 10px" }} onClick={() => void load()}>
            Refresh
          </button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>id</th>
                <th>status</th>
                <th>goal</th>
                <th>created</th>
                <th>updated</th>
                <th>tasks</th>
                <th>verif.</th>
                <th>tools</th>
                <th>model</th>
                <th>tokens</th>
                <th>cost</th>
                <th>budget</th>
                <th>actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((o) => {
                const st = o.status.toLowerCase();
                const usage = o.usage || {};
                const budget = o.budget || {};
                const busy = acting?.id === o.id;
                return (
                  <tr
                    key={o.id}
                    onClick={() => select(o.id)}
                    style={{ cursor: "pointer", outline: selected?.id === o.id ? "1px solid var(--accent)" : "none" }}
                  >
                    <td title={o.id}>{o.id.slice(0, 12)}</td>
                    <td>
                      <span className={`badge ${objStatusClass(o.status)}`}>{o.status}</span>
                    </td>
                    <td className="goal-cell" title={o.goal}>{o.goal}</td>
                    <td title={fmtTime(o.created)}>{fmtAgo(o.created)}</td>
                    <td title={fmtTime(o.updated)}>{fmtAgo(o.updated)}</td>
                    <td>{o.result_summary ? `—` : "—"}</td>
                    <td>
                      {o.verification ? (
                        <span
                          className={`badge ${
                            o.verification === "VERIFIED" ? "b-ok" : o.verification === "FAILED" ? "b-bad" : "b-warn"
                          }`}
                        >
                          {o.verification}
                        </span>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td>{usage.tool_calls ?? 0}/{budget.tool_calls || "∞"}</td>
                    <td>{usage.model_calls ?? 0}/{budget.model_calls || "∞"}</td>
                    <td>{usage.tokens ?? 0}</td>
                    <td>${(usage.money_usd ?? 0).toFixed(4)}</td>
                    <td className="hint">
                      {budget.seconds ? `${Math.round(((usage.seconds ?? 0) / budget.seconds) * 100)}%` : "—"}
                    </td>
                    <td onClick={(e) => e.stopPropagation()}>
                      <div className="row" style={{ gap: 4 }}>
                        {st === "pending" && (
                          <button className="btn mini" disabled={busy} onClick={() => void act(o.id, "run")}>
                            Run
                          </button>
                        )}
                        {["paused", "needs_user", "failed"].includes(st) && (
                          <button className="btn mini" disabled={busy} onClick={() => void act(o.id, "resume")}>
                            Resume
                          </button>
                        )}
                        {(st === "running" || st === "planning") && (
                          <button className="btn mini ghost" disabled={busy} onClick={() => void act(o.id, "pause")}>
                            Pause
                          </button>
                        )}
                        {["pending", "planning", "running", "paused", "needs_user"].includes(st) && (
                          <button className="btn mini ghost" disabled={busy} onClick={() => void act(o.id, "cancel")}>
                            Cancel
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={13} className="hint">
                    no objectives {activeOnly ? "in flight" : "yet"}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

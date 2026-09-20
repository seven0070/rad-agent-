import { useEffect, useState } from "react";
import { ObjectiveRow, RadClient } from "../api";
import { usePolling } from "../hooks/usePolling";
import { VerificationCard } from "./VerificationCard";

function chipClass(v: string | undefined | null) {
  return `chip ${(v || "pending").toLowerCase()}`;
}

/**
 * What tools the control plane exposes + a per-objective trace (verification,
 * tasks) — the read-only evidence surface for a selected objective.
 */
export function ToolsTrace({
  client,
  onOpenObjective,
}: {
  client: RadClient;
  onOpenObjective?: (id: string) => void;
}) {
  const toolsPoll = usePolling(() => client.tools(), { intervalMs: 5000 });
  const tools = toolsPoll.data?.tools || [];

  const [rows, setRows] = useState<ObjectiveRow[]>([]);
  const [selected, setSelected] = useState("");
  const tracePoll = usePolling(() => client.trace(selected), {
    intervalMs: 4000,
    isActive: !!selected,
  });
  const trace = tracePoll.data;

  useEffect(() => {
    let live = true;
    client
      .objectives(false)
      .then((r) => {
        if (!live) return;
        setRows(r.objectives);
        setSelected((prev) => prev || r.objectives[0]?.id || "");
      })
      .catch(() => {});
    return () => {
      live = false;
    };
  }, [client]);

  return (
    <div>
      <h1>Tools &amp; Trace</h1>
      <p className="lead">
        Read-only map of tools the control plane can route, and the trace + verification for an
        objective. No tool execution from the desktop.
      </p>
      <div className="card">
        <h3>Available tools ({tools.length})</h3>
        {tools.length === 0 && <p className="meta">{toolsPoll.error || "no tools reported"}</p>}
        {tools.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>name</th>
                <th>capability</th>
                <th>policy</th>
                <th>description</th>
              </tr>
            </thead>
            <tbody>
              {tools.map((t) => (
                <tr key={t.name}>
                  <td className="mono">{t.name}</td>
                  <td>{t.capability}</td>
                  <td>{t.policy}</td>
                  <td className="meta">{t.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      <div className="card">
        <h3>Trace</h3>
        <label>Objective</label>
        <select value={selected} onChange={(e) => setSelected(e.target.value)}>
          {rows.length === 0 && <option value="">no objectives</option>}
          {rows.map((o) => (
            <option key={o.id} value={o.id}>
              {o.id.slice(0, 12)} · {o.status} · {o.goal.slice(0, 60)}
            </option>
          ))}
        </select>
        {tracePoll.error && <p className="err">{tracePoll.error}</p>}
        {!trace && !tracePoll.error && <p className="meta">select an objective to trace it</p>}
        {trace && (
          <div style={{ marginTop: 12 }}>
            <div className="row" style={{ marginBottom: 8 }}>
              <span className={chipClass(trace.objective.status)}>{trace.objective.status}</span>
              <span className={chipClass(trace.objective.verification)}>
                {trace.objective.verification || "no verified pass"}
              </span>
              <span className="meta mono">{trace.objective.id}</span>
              {onOpenObjective && (
                <button
                  className="btn ghost"
                  style={{ padding: "2px 8px", fontSize: 12 }}
                  onClick={() => onOpenObjective(trace.objective.id)}
                >
                  open detail
                </button>
              )}
            </div>
            <VerificationCard verification={trace.verification} tasks={trace.tasks} />
          </div>
        )}
      </div>
    </div>
  );
}
import { useEffect, useState } from "react";
import { RadClient } from "../api";
import { usePolling } from "../hooks/usePolling";
import { ObjectiveDetail as ObjectiveDetailView } from "./ObjectiveDetail";

function chipClass(v: string) {
  return `chip ${v.toLowerCase()}`;
}

/**
 * Live "active run" surface. Polls /v1/status, lets the user pick which running
 * objective to watch, and composes the full ObjectiveDetail view for it.
 */
export function ActiveRun({
  client,
  onBack,
  onOpenObjective,
}: {
  client: RadClient;
  onBack?: () => void;
  onOpenObjective?: (id: string) => void;
}) {
  const poll = usePolling(() => client.status(), { intervalMs: 5000 });
  const runs = poll.data?.running_objectives || [];
  const byStatus = poll.data?.objectives?.by_status || {};
  const [selected, setSelected] = useState("");

  useEffect(() => {
    if (selected && runs.includes(selected)) return;
    setSelected(runs[0] || "");
  }, [runs, selected]);

  const counts = Object.entries(byStatus)
    .filter(([, n]) => n > 0)
    .map(([s, n]) => (
      <span key={s} className={chipClass(s)}>
        {s} {n}
      </span>
    ));

  return (
    <div>
      <h1>Active Run</h1>
      <p className="lead">
        Live view of what the control plane is executing. Desktop shows status from the Python
        core — it does not run or schedule objectives itself.
      </p>
      {poll.error && <p className="err">{poll.error}</p>}
      <div className="row" style={{ marginBottom: 4 }}>
        {runs.length === 0 && <span className="chip pending">no running objectives</span>}
        {runs.map((r) => (
          <button
            key={r}
            className={`chip running ${selected === r ? "sel" : ""}`}
            onClick={() => setSelected(r)}
            title={r}
          >
            {r.slice(0, 12)}
          </button>
        ))}
      </div>
      {counts.length > 0 && <div className="row">{counts}</div>}
      {selected ? (
        <ObjectiveDetailView key={selected} client={client} id={selected} onBack={onBack} onOpenObjective={onOpenObjective} />
      ) : (
        <div className="card">
          <p className="meta">
            No objective is currently running. Create one from Objectives, or resume a PENDING one.
          </p>
        </div>
      )}
    </div>
  );
}
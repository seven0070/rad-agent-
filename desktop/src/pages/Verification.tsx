/** Verification center. Machine verification only — the backend Verifier is the
 *  single source of VERIFIED. The frontend displays; it never manufactures it. */
import { useEffect, useState } from "react";
import { ObjectiveRow, TaskRow } from "../api";
import { useRad } from "../ctx";
import { fmtTime, redactText, taskStateClass } from "../util";

interface ObjCheck {
  ok: boolean;
  level?: string;
  detail?: string;
  [k: string]: unknown;
}

export default function Verification() {
  const { client, selected } = useRad();
  const [obj, setObj] = useState<(ObjectiveRow & { verification?: Record<string, unknown> }) | null>(null);
  const [tasks, setTasks] = useState<TaskRow[]>([]);
  const [err, setErr] = useState("");
  const id = selected?.id;

  useEffect(() => {
    if (!id) return;
    let stop = false;
    const tick = async () => {
      try {
        const o = await client.objective(id);
        if (stop) return;
        setObj(o as (ObjectiveRow & { verification?: Record<string, unknown> }));
        setTasks(o.tasks || []);
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

  if (!id) {
    return (
      <div>
        <h1>Verification</h1>
        <p className="lead">Select an objective to inspect machine verification.</p>
      </div>
    );
  }

  const ver = ((obj?.verification as Record<string, unknown> | undefined)?.objective as Record<string, unknown>) || {};
  const status = String(ver.status || (obj?.verification || "") || "");
  const results = (ver.results as ObjCheck[]) || [];
  const unverified = (ver.tasks_unverified as string[]) || [];

  return (
    <div>
      <h1>Verification</h1>
      <p className="lead">
        Invariant: a model saying <b>DONE</b> is never VERIFIED. Only backend machine
        checks produce VERIFIED.
      </p>
      {err && <p className="err">{err}</p>}

      <div className={`ver-banner ${status === "VERIFIED" ? "vb-ok" : status === "FAILED" ? "vb-bad" : "vb-warn"}`}>
        <b style={{ fontSize: 18 }}>{status || "UNVERIFIED"}</b>
        <span>
          objective {id}
          {ver.at ? ` · ${fmtTime(Number(ver.at))}` : ""}
        </span>
      </div>

      {results.length > 0 && (
        <div className="card">
          <label>Objective checks (machine-evaluated)</label>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>result</th>
                  <th>level</th>
                  <th>detail</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, i) => (
                  <tr key={i}>
                    <td>
                      <span className={`badge ${r.ok ? "b-ok" : "b-bad"}`}>{r.ok ? "PASS" : "FAIL"}</span>
                    </td>
                    <td className="hint">{String(r.level || "machine")}</td>
                    <td className="hint" style={{ maxWidth: 560 }}>
                      {redactText(String(r.detail || "")).slice(0, 400)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {unverified.length > 0 && (
        <div className="banner">
          {unverified.length} task(s) completed without machine verification: {unverified.join(", ")}.
          The objective is recorded accordingly — not silently verified.
        </div>
      )}

      <div className="card">
        <label>Task verification</label>
        {tasks.length === 0 && <div className="hint">no tasks yet</div>}
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>task</th>
                <th>state</th>
                <th>verification</th>
                <th>checks</th>
                <th>summary</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((t) => (
                <tr key={t.id}>
                  <td className="hint" title={t.text}>{redactText((t.text || t.id).slice(0, 50))}</td>
                  <td>
                    <span className={`badge ${taskStateClass(t.status)}`}>{t.status}</span>
                  </td>
                  <td>
                    {t.verification?.status ? (
                      <span
                        className={`badge ${
                          t.verification.status === "VERIFIED" ? "b-ok" : t.verification.status === "FAILED" ? "b-bad" : "b-warn"
                        }`}
                      >
                        {t.verification.status}
                      </span>
                    ) : (
                      <span className="hint">—</span>
                    )}
                  </td>
                  <td className="hint">{(t.checks || []).length}</td>
                  <td className="hint" style={{ maxWidth: 420 }}>
                    {redactText(String(t.verification?.summary || "")).slice(0, 220)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

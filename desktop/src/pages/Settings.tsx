/** Settings + backend lifecycle + usage. Writes are limited to the backend's
 *  /v1/settings whitelist; budgets and policy stay untouched. */
import { useCallback, useEffect, useState } from "react";
import { ApiError, Settings, UsageRollup } from "../api";
import { backendRestart, isTauri } from "../backend";
import { useRad } from "../ctx";

export default function SettingsPage({ onShutdown }: { onShutdown: () => void }) {
  const { client, status, refresh: onRefresh } = useRad();
  const [s, setS] = useState<Settings | null>(null);
  const [usage, setUsage] = useState<UsageRollup | null>(null);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const [lifecycle, setLifecycle] = useState("");

  const load = useCallback(async () => {
    try {
      const [st, us] = await Promise.all([client.settings(), client.usage()]);
      setS(st);
      setUsage(us);
      setErr("");
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    }
  }, [client]);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async () => {
    if (!s) return;
    setErr("");
    setOk("");
    try {
      const next = await client.setSettings({
        workspace: s.workspace,
        free_lock: s.free_lock,
        model: s.model,
        force_provider: s.force_provider,
      });
      setS(next);
      setOk("saved (backend-validated)");
      await onRefresh();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    }
  };

  const restartBackend = async () => {
    setLifecycle("restarting backend…");
    try {
      const info = await backendRestart();
      setLifecycle(`backend ${info.running ? "running" : "stopped"} on port ${info.port}`);
    } catch (e) {
      setLifecycle(`restart failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  if (!s) return <p className="lead">Loading settings…</p>;

  return (
    <div>
      <h1>Settings</h1>
      <p className="lead">{s.note}</p>

      <div className="card">
        <label>Workspace (where tools operate)</label>
        <input value={s.workspace} onChange={(e) => setS({ ...s, workspace: e.target.value })} />
        <div className="row" style={{ marginTop: 10 }}>
          <label style={{ marginBottom: 0, flex: 1 }}>Pinned model</label>
          <input
            value={s.model || ""}
            onChange={(e) => setS({ ...s, model: e.target.value || null })}
            style={{ maxWidth: 280 }}
          />
        </div>
        <label style={{ marginTop: 10 }}>
          <input
            type="checkbox"
            checked={s.free_lock}
            onChange={(e) => setS({ ...s, free_lock: e.target.checked })}
            style={{ width: "auto", marginRight: 8 }}
          />
          free-lock (paid providers impossible)
        </label>
        <div className="row" style={{ marginTop: 12 }}>
          <button className="btn" onClick={() => void save()}>
            Save
          </button>
        </div>
        {err && <p className="err">{err}</p>}
        {ok && <p className="ok">{ok}</p>}
      </div>

      <div className="card">
        <label>RAD backend</label>
        <div className="kv"><span>version</span><b>{status?.version || "—"}</b></div>
        <div className="kv"><span>home</span><b>{status?.home || "—"}</b></div>
        <div className="kv"><span>auto (config)</span><b>{String(s.auto)}</b></div>
        <div className="kv"><span>tool router</span><b>{s.tool_router} (off unless set in CLI — never raised here)</b></div>
        <div className="kv"><span>API port</span><b>{s.api_port}</b></div>
        {lifecycle && <p className="hint" style={{ marginTop: 8 }}>{lifecycle}</p>}
        <div className="row" style={{ marginTop: 10 }}>
          {isTauri() && (
            <>
              <button className="btn ghost" onClick={() => void restartBackend()}>
                Restart backend
              </button>
              <button className="btn warn" onClick={onShutdown}>
                Shut down backend
              </button>
            </>
          )}
        </div>
      </div>

      {usage && (
        <div className="card">
          <label>Usage (persisted per-objective rollup — no invented quotas)</label>
          <div className="kv"><span>objectives</span><b>{usage.count}</b></div>
          <div className="kv"><span>tool calls</span><b>{usage.tool_calls}</b></div>
          <div className="kv"><span>model calls</span><b>{usage.model_calls}</b></div>
          <div className="kv"><span>tokens</span><b>{usage.tokens}</b></div>
          <div className="kv"><span>paid spend</span><b>${usage.money_usd.toFixed(4)}</b></div>
          <div className="hint" style={{ marginTop: 6 }}>{usage.note}</div>
          {usage.objectives.length > 0 && (
            <div className="table-wrap" style={{ marginTop: 10 }}>
              <table>
                <thead>
                  <tr>
                    <th>objective</th>
                    <th>status</th>
                    <th>tools</th>
                    <th>model</th>
                    <th>tokens</th>
                    <th>cost</th>
                  </tr>
                </thead>
                <tbody>
                  {usage.objectives.map((o) => (
                    <tr key={o.id}>
                      <td className="hint" title={o.goal}>{o.id.slice(0, 12)} · {o.goal.slice(0, 40)}</td>
                      <td className="hint">{o.status}</td>
                      <td className="hint">{o.tool_calls}</td>
                      <td className="hint">{o.model_calls}</td>
                      <td className="hint">{o.tokens}</td>
                      <td className="hint">${o.money_usd.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

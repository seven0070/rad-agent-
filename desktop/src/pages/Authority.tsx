/** Authority center over the existing /v1/authority. The backend is the only
 *  source of authority state — nothing is mirrored in browser storage. */
import { useCallback, useEffect, useState } from "react";
import { ApiError, Profile, RadEvent } from "../api";
import { useRad } from "../ctx";
import { fmtTime } from "../util";

const PROFILES: Profile[] = ["SAFE", "STANDARD", "AUTONOMOUS", "UNRESTRICTED", "CUSTOM"];

export default function AuthorityPage() {
  const { client, auth, onAuth } = useRad();
  const [profile, setProfile] = useState<Profile>(auth.profile);
  const [confirmU, setConfirmU] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const [busy, setBusy] = useState(false);
  const [changes, setChanges] = useState<RadEvent[]>([]);
  const [caps, setCaps] = useState<Record<string, string>>({});
  const [hosts, setHosts] = useState("");
  const [extraPaths, setExtraPaths] = useState("");
  const [workspaceOnly, setWorkspaceOnly] = useState(auth.scopes.workspace_only);

  const loadChanges = useCallback(async () => {
    for (const kind of ["AUTHORITY", "CAPABILITY", "SCOPE", "CONFIRMATION"]) {
      try {
        const r = await client.eventsGlobal(20, kind);
        setChanges((prev) => {
          const have = new Set(prev.map((e) => e.seq));
          return [...prev, ...r.events.filter((e) => !have.has(e.seq))].sort((a, b) => a.seq - b.seq).slice(-30);
        });
      } catch {
        /* non-fatal */
      }
    }
  }, [client]);

  useEffect(() => {
    void loadChanges();
    setProfile(auth.profile);
    setWorkspaceOnly(auth.scopes.workspace_only);
    setHosts(auth.scopes.hosts.join(", "));
    setExtraPaths(auth.scopes.extra_paths.join(", "));
    const custom: Record<string, string> = {};
    if (auth.profile === "CUSTOM") {
      for (const [name, info] of Object.entries(auth.capabilities)) custom[name] = info.effect;
    }
    setCaps(custom);
  }, [auth]);

  const apply = async () => {
    setBusy(true);
    setErr("");
    setOk("");
    try {
      const body: Parameters<typeof client.setAuthority>[0] = { profile };
      if (profile === "UNRESTRICTED") body.confirm_unrestricted = confirmU;
      if (profile === "CUSTOM" && Object.keys(caps).length) body.capabilities = caps;
      const scopes: Record<string, unknown> = {
        workspace_only: workspaceOnly,
        extra_paths: extraPaths.split(",").map((s) => s.trim()).filter(Boolean),
        hosts: hosts.split(",").map((s) => s.trim().toLowerCase()).filter(Boolean),
      };
      body.scopes = scopes;
      const next = await client.setAuthority(body);
      onAuth(next);
      setOk(`profile set to ${next.profile}`);
      void loadChanges();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const groups = Object.entries(auth.capabilities);

  return (
    <div>
      <h1>Authority</h1>
      <p className="lead">
        User → authority profile → capability / scope / confirmation → existing{" "}
        <b>Policy.decide</b> → executor → tool. The desktop cannot widen grants; it only
        requests changes the backend accepts.
      </p>

      {auth.unrestricted && (
        <div className="banner">
          <b>UNRESTRICTED</b> is explicitly user-authorized autonomy — not a hidden path.
          Policy.decide, the executor, hard blocks, budgets, audit, provenance and
          verification all remain in force.
        </div>
      )}

      <div className="grid auth-grid">
        <div className="card">
          <label>Current profile</label>
          <span className={`pill ${auth.profile} fs-14`}>
            {auth.profile}
          </span>
          <p className="lead mt-10">{auth.blurb}</p>
          <label>Confirmation</label>
          <div>
            {auth.confirmation}{" "}
            {auth.confirmation_is_automatic && (
              <span className="hint">(ASK→ALLOW; DENY / hard / budget unchanged)</span>
            )}
          </div>
          <label className="mt-10">Scopes</label>
          <div className="hint">
            workspace_only={String(auth.scopes.workspace_only)}
            {auth.scopes.extra_paths.length ? ` · extra: ${auth.scopes.extra_paths.join(", ")}` : ""}
            {auth.scopes.hosts.length ? ` · hosts: ${auth.scopes.hosts.join(", ")}` : ""}
          </div>
          <label className="mt-10">Budget (existing control-plane defaults — not raised here)</label>
          <div className="hint">
            tools {auth.budgets.tool_calls} · model {auth.budgets.model_calls} · retries {auth.budgets.retries}
          </div>
        </div>

        <div className="card">
          <label>Set profile</label>
          <div className="grid prof-grid">
            {PROFILES.map((p) => (
              <button
                key={p}
                className={`prof ${profile === p ? "active" : ""} prof-${p.toLowerCase()}`}
                onClick={() => setProfile(p)}
                title={
                  p === "SAFE" ? "Confirmation-heavy, narrow grants"
                    : p === "STANDARD" ? "Existing RAD defaults"
                    : p === "AUTONOMOUS" ? "Reduced confirmation; enforcement remains"
                    : p === "UNRESTRICTED" ? "Explicitly authorized autonomy (not a bypass)"
                    : "Per-capability effects"
                }
              >
                {p}
              </button>
            ))}
          </div>
          {profile === "UNRESTRICTED" && (
            <label className="mt-10">
              <input
                type="checkbox"
                checked={confirmU}
                onChange={(e) => setConfirmU(e.target.checked)}
                className="cb-inline"
              />
              I explicitly authorize UNRESTRICTED autonomy within the configured scope.
              (The backend rejects the request without this.)
            </label>
          )}

          {profile === "CUSTOM" && (
            <div className="mt-10">
              <label>Per-capability effects (leave empty to keep current)</label>
              {groups.map(([name, info]) => (
                <div className="row mb-4" key={name}>
                  <span className="hint w-150">{name}</span>
                  <select
                    className="w-110"
                    value={caps[name] ?? info.effect}
                    onChange={(e) => setCaps({ ...caps, [name]: e.target.value })}
                  >
                    {["ALLOW", "ASK", "LIMITED", "DENY"].map((x) => (
                      <option key={x}>{x}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>
          )}

          <label className="mt-10">Scope</label>
          <label>
            <input
              type="checkbox"
              checked={workspaceOnly}
              onChange={(e) => setWorkspaceOnly(e.target.checked)}
              className="cb-inline"
            />
            workspace-only filesystem
          </label>
          <input
            className="mt-6"
            placeholder="extra paths (comma-separated)"
            value={extraPaths}
            onChange={(e) => setExtraPaths(e.target.value)}
          />
          <input
            className="mt-6"
            placeholder="allowed hosts (comma-separated)"
            value={hosts}
            onChange={(e) => setHosts(e.target.value)}
          />
          <div className="row mt-12">
            <button className={profile === "UNRESTRICTED" ? "btn warn" : "btn"} disabled={busy} onClick={() => void apply()}>
              {busy ? "Applying…" : "Apply profile"}
            </button>
          </div>
          {err && <p className="err">{err}</p>}
          {ok && <p className="ok">{ok}</p>}
        </div>
      </div>

      <div className="card">
        <label>Capabilities under this profile (effect → policy capability)</label>
        <div className="grid">
          {groups.map(([name, info]) => (
            <div key={name} className={`cap ${info.granted ? "" : "denied"}`}>
              <b>{name}</b>
              <div className="eff">
                <span
                  className={`badge ${
                    info.effect === "ALLOW" ? "b-ok" : info.effect === "DENY" ? "b-bad" : "b-warn"
                  }`}
                >
                  {info.effect}
                </span>{" "}
                → {info.capability}
              </div>
            </div>
          ))}
        </div>
        <p className="hint mt-8">
          {auth.passthrough
            ? "STANDARD: no extra grant/scope layer — the existing policy defaults apply."
            : "This profile imposes an authority floor on top of Policy.decide; it never widens a DENY or LIMITED."}{" "}
          credentials stay denied in every profile, including UNRESTRICTED.
        </p>
      </div>

      <div className="card">
        <label>Authority changes (audited events)</label>
        {changes.length === 0 && <div className="hint">no recorded changes</div>}
        {changes.map((e) => (
          <div key={e.seq} className="hint mb-4">
            {fmtTime(e.at)} · {e.kind}{" "}
            {e.data.profile ? `→ ${String(e.data.profile)}` : ""}
            {e.data.capability ? ` ${String(e.data.capability)}=${String(e.data.effect || e.data.effect === 0 ? "" : e.data.effect)}` : ""}
            {e.data.confirmation ? ` confirmation=${String(e.data.confirmation)}` : ""}
            {e.data.actor ? ` (by ${String(e.data.actor)})` : ""}
          </div>
        ))}
      </div>
    </div>
  );
}

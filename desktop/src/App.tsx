import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ApiError,
  AuthoritySnapshot,
  ObjectiveRow,
  RadClient,
  Settings,
  Status,
  TaskRow,
  Verification,
} from "./api";
import {
  apiBase,
  apiToken,
  backendInfo,
  backendStart,
  backendStop,
  isTauri,
} from "./backend";
import { ActiveRun } from "./views/ActiveRun";
import { Memory } from "./views/Memory";
import { ObjectiveDetail as ObjectiveDetailView } from "./views/ObjectiveDetail";
import { ToolsTrace } from "./views/ToolsTrace";
import { VerificationCard } from "./views/VerificationCard";

type Page =
  | "chat"
  | "active"
  | "objectives"
  | "objective"
  | "tasks"
  | "tools"
  | "memory"
  | "verification"
  | "permissions"
  | "settings";

const PAGES: { id: Page; label: string }[] = [
  { id: "chat", label: "Chat" },
  { id: "active", label: "Active" },
  { id: "objectives", label: "Objectives" },
  { id: "tasks", label: "Tasks" },
  { id: "tools", label: "Tools" },
  { id: "memory", label: "Memory" },
  { id: "verification", label: "Verification" },
  { id: "permissions", label: "Permissions" },
  { id: "settings", label: "Settings" },
];

function chipClass(v: string | undefined | null) {
  return `chip ${(v || "pending").toLowerCase()}`;
}

export default function App() {
  const [page, setPage] = useState<Page>("chat");
  const [objectiveId, setObjectiveId] = useState<string | null>(null);
  const [client, setClient] = useState<RadClient | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [auth, setAuth] = useState<AuthoritySnapshot | null>(null);
  const [backend, setBackend] = useState<"connected" | "connecting" | "down">("connecting");
  const [error, setError] = useState("");
  const [manualBase, setManualBase] = useState(apiBase());
  const [manualToken, setManualToken] = useState("");

  const openObjective = useCallback((id: string) => {
    setObjectiveId(id);
    setPage("objective");
  }, []);

  const backObjective = useCallback(() => {
    setPage("objectives");
  }, []);

  const connect = useCallback(async (base: string, token: string) => {
    const c = new RadClient(base, token);
    const h = await c.health();
    if (!h.ok) throw new Error("backend not healthy");
    const [st, a] = await Promise.all([c.status(), c.authority()]);
    setClient(c);
    setStatus(st);
    setAuth(a);
    setBackend("connected");
    setError("");
  }, []);

  const boot = useCallback(async () => {
    setBackend("connecting");
    setError("");
    try {
      if (isTauri()) {
        const info = await backendInfo();
        let token = "";
        try {
          await backendStart(info.port || 7331);
        } catch {
          /* may already be running externally */
        }
        token = await apiToken();
        if (!token) throw new Error("no API token — start `rad serve` once to create ~/.rad/api.token");
        await connect(apiBase(info.port || 7331), token);
        return;
      }
      const envTok = import.meta.env.VITE_RAD_TOKEN || "";
      if (envTok) {
        await connect(apiBase(), envTok);
        return;
      }
      setBackend("down");
    } catch (e) {
      setBackend("down");
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [connect]);

  useEffect(() => {
    void boot();
  }, [boot]);

  const refresh = useCallback(async () => {
    if (!client) return;
    const [st, a] = await Promise.all([client.status(), client.authority()]);
    setStatus(st);
    setAuth(a);
  }, [client]);

  const shutdown = useCallback(async () => {
    try {
      await backendStop();
    } finally {
      setClient(null);
      setBackend("down");
    }
  }, []);

  const model = status?.chain?.[0] || "no brain";

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          RAD Desktop
          <span>0.1.0-alpha · authority foundation</span>
        </div>
        <nav className="nav">
          {PAGES.map((p) => (
            <button
              key={p.id}
              className={page === p.id ? "active" : ""}
              onClick={() => setPage(p.id)}
            >
              {p.label}
            </button>
          ))}
        </nav>
      </aside>
      <main className="main">
        {backend !== "connected" || !client || !auth ? (
          <Connect
            backend={backend}
            error={error}
            manualBase={manualBase}
            manualToken={manualToken}
            setManualBase={setManualBase}
            setManualToken={setManualToken}
            onRetry={boot}
            onManual={() => connect(manualBase, manualToken).catch((e) => setError(String(e)))}
          />
        ) : (
          <Surface
            page={page}
            client={client}
            auth={auth}
            status={status}
            objectiveId={objectiveId}
            onOpenObjective={openObjective}
            onBackObjective={backObjective}
            onAuth={setAuth}
            onRefresh={refresh}
          />
        )}
      </main>
      <footer className="status">
        <span>
          <i className={`dot ${backend === "connected" ? "ok" : "off"}`} />
          {backend === "connected" ? "backend connected" : backend}
        </span>
        <span className={`pill ${auth?.profile || "STANDARD"}`}>{auth?.profile || "—"}</span>
        <span>{model}</span>
        <span>
          budget {auth?.budgets.tool_calls ?? 60} tools / {auth?.budgets.model_calls ?? 80} model
        </span>
        <span style={{ marginLeft: "auto" }}>
          {isTauri() && (
            <button className="btn ghost" style={{ padding: "2px 8px" }} onClick={() => void shutdown()}>
              shut down
            </button>
          )}
        </span>
      </footer>
    </div>
  );
}

function Connect(props: {
  backend: string;
  error: string;
  manualBase: string;
  manualToken: string;
  setManualBase: (v: string) => void;
  setManualToken: (v: string) => void;
  onRetry: () => void;
  onManual: () => void;
}) {
  return (
    <div className="connect">
      <h1>Connect to RAD</h1>
      <p className="lead">
        Desktop is a surface over the existing Python API. It cannot run tools, raise budgets,
        or bypass Policy.decide.
      </p>
      {props.error && <p className="err">{props.error}</p>}
      <div className="card">
        <button className="btn" onClick={props.onRetry}>
          {props.backend === "connecting" ? "Connecting…" : "Launch / reconnect"}
        </button>
      </div>
      <div className="card">
        <label>API base</label>
        <input value={props.manualBase} onChange={(e) => props.setManualBase(e.target.value)} />
        <label style={{ marginTop: 10 }}>Bearer token</label>
        <input
          value={props.manualToken}
          onChange={(e) => props.setManualToken(e.target.value)}
          placeholder="from ~/.rad/api.token"
        />
        <div className="row" style={{ marginTop: 12 }}>
          <button className="btn ghost" onClick={props.onManual}>
            Connect with token
          </button>
        </div>
      </div>
    </div>
  );
}

function Surface(props: {
  page: Page;
  client: RadClient;
  auth: AuthoritySnapshot;
  status: Status | null;
  objectiveId: string | null;
  onOpenObjective: (id: string) => void;
  onBackObjective: () => void;
  onAuth: (a: AuthoritySnapshot) => void;
  onRefresh: () => Promise<void>;
}) {
  switch (props.page) {
    case "chat":
      return <Chat client={props.client} />;
    case "active":
      return (
        <ActiveRun
          client={props.client}
          onOpenObjective={props.onOpenObjective}
          onBack={props.onBackObjective}
        />
      );
    case "objectives":
      return <Objectives client={props.client} onView={props.onOpenObjective} />;
    case "objective":
      return props.objectiveId ? (
        <ObjectiveDetailView
          key={props.objectiveId}
          client={props.client}
          id={props.objectiveId}
          onBack={props.onBackObjective}
          onOpenObjective={props.onOpenObjective}
        />
      ) : (
        <div>
          <h1>Objective</h1>
          <p className="lead">Pick an objective from the Objectives page.</p>
          <button className="btn" onClick={props.onBackObjective}>
            ← Objectives
          </button>
        </div>
      );
    case "tasks":
      return <Tasks client={props.client} />;
    case "tools":
      return <ToolsTrace client={props.client} onOpenObjective={props.onOpenObjective} />;
    case "memory":
      return <Memory client={props.client} />;
    case "verification":
      return <VerificationPage client={props.client} onOpenObjective={props.onOpenObjective} />;
    case "permissions":
      return <Permissions client={props.client} auth={props.auth} onAuth={props.onAuth} />;
    case "settings":
      return <SettingsPage client={props.client} status={props.status} onRefresh={props.onRefresh} />;
    default: {
      const _n: never = props.page;
      return <p className="err">unknown page {_n}</p>;
    }
  }
}

function Chat({ client }: { client: RadClient }) {
  const [text, setText] = useState("");
  const [msgs, setMsgs] = useState<Array<{ who: "user" | "jerry"; text: string }>>([]);
  const [busy, setBusy] = useState(false);
  const send = async () => {
    const t = text.trim();
    if (!t || busy) return;
    setText("");
    setMsgs((m) => [...m, { who: "user", text: t }]);
    setBusy(true);
    try {
      const r = await client.chat(t);
      setMsgs((m) => [
        ...m,
        { who: "jerry", text: r.via ? `${r.reply}\n— via ${r.via}` : r.reply },
      ]);
    } catch (e) {
      setMsgs((m) => [...m, { who: "jerry", text: e instanceof Error ? e.message : String(e) }]);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="chat">
      <h1>Jerry</h1>
      <p className="lead">
        Operator layer over the RAD session. Tools still pass Policy.decide and the executor.
        Jerry cannot run a private tool path.
      </p>
      <div className="msgs">
        {msgs.length === 0 && (
          <div className="bubble jerry">Ask anything. Objectives you create go through the control plane.</div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`bubble ${m.who}`}>
            {m.text}
          </div>
        ))}
      </div>
      <div className="row">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send();
            }
          }}
          placeholder="Message Jerry…"
        />
        <button className="btn" disabled={busy} onClick={() => void send()}>
          Send
        </button>
      </div>
    </div>
  );
}

function Objectives({
  client,
  onView,
}: {
  client: RadClient;
  onView: (id: string) => void;
}) {
  const [rows, setRows] = useState<ObjectiveRow[]>([]);
  const [activeOnly, setActiveOnly] = useState(false);
  const [goal, setGoal] = useState("");
  const [detail, setDetail] = useState<string>("");
  const [traceId, setTraceId] = useState<string>("");
  const [err, setErr] = useState("");
  const load = useCallback(async () => {
    const r = await client.objectives(activeOnly);
    setRows(r.objectives);
  }, [client, activeOnly]);
  useEffect(() => {
    void load();
  }, [load]);
  const create = async () => {
    setErr("");
    try {
      const o = await client.createObjective(goal);
      setGoal("");
      setDetail(o.note || (o.started ? "started" : "created PENDING"));
      await load();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    }
  };
  const inspect = async (id: string) => {
    setTraceId(id);
    const t = await client.trace(id);
    setDetail(JSON.stringify({ objective_id: id, verification: t.verification, tasks: t.tasks }, null, 2));
  };
  return (
    <div>
      <h1>Objectives</h1>
      <p className="lead">Existing control plane. Desktop displays objectives, tasks and verification — it is not a React task engine.</p>
      <div className="card">
        <label>New objective</label>
        <input value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="goal" />
        <div className="row" style={{ marginTop: 10 }}>
          <button className="btn" onClick={() => void create()}>
            Create
          </button>
          <button className="btn ghost" onClick={() => void load()}>
            Refresh
          </button>
          <label className="row" style={{ marginLeft: 12, width: "auto" }}>
            <input
              type="checkbox"
              checked={activeOnly}
              onChange={(e) => setActiveOnly(e.target.checked)}
              style={{ width: "auto", marginRight: 6 }}
            />
            active only
          </label>
        </div>
        {err && <p className="err">{err}</p>}
        {detail && <pre className="lead" style={{ whiteSpace: "pre-wrap" }}>{detail}</pre>}
      </div>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>id</th>
              <th>status</th>
              <th>verification</th>
              <th>goal</th>
              <th>actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((o) => (
              <tr key={o.id} className={o.id === traceId ? "sel-row" : ""}>
                <td>{o.id.slice(0, 12)}</td>
                <td><span className={chipClass(o.status)}>{o.status}</span></td>
                <td><span className={chipClass(o.verification)}>{o.verification || "—"}</span></td>
                <td>{o.goal}</td>
                <td>
                  <div className="row">
                    <button className="btn ghost" style={{ padding: "1px 6px", fontSize: 11 }} onClick={() => void inspect(o.id)}>
                      trace
                    </button>
                    <button className="btn ghost" style={{ padding: "1px 6px", fontSize: 11 }} onClick={() => onView(o.id)}>
                      view
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Tasks({ client }: { client: RadClient }) {
  const [rows, setRows] = useState<TaskRow[]>([]);
  useEffect(() => {
    void client.tasks().then((r) => setRows(r.tasks));
  }, [client]);
  return (
    <div>
      <h1>Tasks</h1>
      <p className="lead">Read-only view of control-plane tasks and their verification status.</p>
      <div className="card">
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
            {rows.map((t) => (
              <tr key={`${t.objective_id}-${t.id}`}>
                <td>{t.status}</td>
                <td>{t.verification?.status || "—"}</td>
                <td>{t.title || t.text || t.id}</td>
                <td>{t.goal || t.objective_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Permissions({
  client,
  auth,
  onAuth,
}: {
  client: RadClient;
  auth: AuthoritySnapshot;
  onAuth: (a: AuthoritySnapshot) => void;
}) {
  const [profile, setProfile] = useState(auth.profile);
  const [confirmU, setConfirmU] = useState(false);
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  const apply = async () => {
    setErr("");
    setOk("");
    try {
      const next = await client.setAuthority({
        profile,
        confirm_unrestricted: profile === "UNRESTRICTED" ? confirmU : undefined,
      });
      onAuth(next);
      setOk(`profile ${next.profile}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };
  const groups = useMemo(() => Object.entries(auth.capabilities), [auth]);
  return (
    <div>
      <h1>Permissions</h1>
      <p className="lead">
        Authority is what is allowed. Scope is how far. Confirmation is whether to ask.
        Budget and Policy.decide stay in the Python core.
      </p>
      {auth.unrestricted && (
        <div className="banner">
          UNRESTRICTED is explicitly user-authorized autonomy — not a hidden or “unsafe by
          definition” path. Hard layer, executor, budgets, audit, provenance and verification remain.
        </div>
      )}
      <div className="card">
        <label>Authority profile</label>
        <select value={profile} onChange={(e) => setProfile(e.target.value as typeof profile)}>
          {["SAFE", "STANDARD", "AUTONOMOUS", "UNRESTRICTED", "CUSTOM"].map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <p className="lead" style={{ marginTop: 10 }}>{auth.blurb}</p>
        {profile === "UNRESTRICTED" && (
          <label>
            <input
              type="checkbox"
              checked={confirmU}
              onChange={(e) => setConfirmU(e.target.checked)}
              style={{ width: "auto", marginRight: 8 }}
            />
            I explicitly authorize UNRESTRICTED autonomy within configured scope
          </label>
        )}
        <div className="row" style={{ marginTop: 12 }}>
          <button className={profile === "UNRESTRICTED" ? "btn warn" : "btn"} onClick={() => void apply()}>
            Apply profile
          </button>
        </div>
        {err && <p className="err">{err}</p>}
        {ok && <p className="ok">{ok}</p>}
      </div>
      <div className="card">
        <label>Confirmation</label>
        <div>{auth.confirmation} {auth.confirmation_is_automatic ? "(ASK→ALLOW; DENY/hard/budget unchanged)" : ""}</div>
        <label style={{ marginTop: 10 }}>Scope</label>
        <div>
          workspace_only={String(auth.scopes.workspace_only)}
          {auth.scopes.extra_paths.length ? ` extra=${auth.scopes.extra_paths.join(", ")}` : ""}
          {auth.scopes.hosts.length ? ` hosts=${auth.scopes.hosts.join(", ")}` : ""}
        </div>
        <label style={{ marginTop: 10 }}>Budget (existing defaults — not raised)</label>
        <div>
          tools {auth.budgets.tool_calls} · model {auth.budgets.model_calls} · retries {auth.budgets.retries}
        </div>
      </div>
      <div className="grid">
        {groups.map(([name, info]) => (
          <div key={name} className={`cap ${info.granted ? "" : "denied"}`}>
            <b>{name}</b>
            <div className="eff">
              {info.effect} → {info.capability}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SettingsPage({
  client,
  status,
  onRefresh,
}: {
  client: RadClient;
  status: Status | null;
  onRefresh: () => Promise<void>;
}) {
  const [s, setS] = useState<Settings | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    void client.settings().then(setS);
  }, [client]);
  if (!s) return <p className="lead">Loading settings…</p>;
  const save = async () => {
    setErr("");
    try {
      const next = await client.setSettings({
        workspace: s.workspace,
        free_lock: s.free_lock,
        model: s.model,
        force_provider: s.force_provider,
      });
      setS(next);
      await onRefresh();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };
  return (
    <div>
      <h1>Settings</h1>
      <p className="lead">{s.note}</p>
      <div className="card">
        <label>Workspace</label>
        <input value={s.workspace} onChange={(e) => setS({ ...s, workspace: e.target.value })} />
        <label style={{ marginTop: 10 }}>Pinned model</label>
        <input value={s.model || ""} onChange={(e) => setS({ ...s, model: e.target.value || null })} />
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
      </div>
      <div className="card">
        <div>Home: {status?.home}</div>
        <div>Needle / tool_router: {s.tool_router} (off unless you set it in CLI)</div>
        <div>Version: {status?.version}</div>
      </div>
    </div>
  );
}

function VerificationPage({
  client,
  onOpenObjective,
}: {
  client: RadClient;
  onOpenObjective: (id: string) => void;
}) {
  const [rows, setRows] = useState<ObjectiveRow[]>([]);
  const [rowsErr, setRowsErr] = useState("");
  const [id, setId] = useState("");
  const [trace, setTrace] = useState<{
    objective: ObjectiveRow;
    tasks: TaskRow[];
    verification: Verification;
  } | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    void client
      .objectives()
      .then((r) => setRows(r.objectives))
      .catch((e) => setRowsErr(e instanceof Error ? e.message : String(e)));
  }, [client]);

  useEffect(() => {
    if (!id) return;
    let live = true;
    const load = async () => {
      try {
        const t = await client.trace(id);
        if (live) {
          setTrace(t);
          setErr("");
        }
      } catch (e) {
        if (live) setErr(e instanceof Error ? e.message : String(e));
      }
    };
    void load();
  }, [id, client]);

  return (
    <div>
      <h1>Verification</h1>
      <p className="lead">
        The desktop never computes VERIFIED — it only displays the control-plane pass/fail
        status. {rowsErr}
      </p>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>id</th>
              <th>status</th>
              <th>verification</th>
              <th>goal</th>
              <th>actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((o) => (
              <tr key={o.id} className={o.id === id ? "sel-row" : ""}>
                <td>{o.id.slice(0, 12)}</td>
                <td><span className={chipClass(o.status)}>{o.status}</span></td>
                <td><span className={chipClass(o.verification)}>{o.verification || "—"}</span></td>
                <td>{o.goal}</td>
                <td>
                  <div className="row">
                    <button className="btn ghost" style={{ padding: "1px 6px", fontSize: 11 }} onClick={() => setId(o.id)}>
                      trace
                    </button>
                    <button className="btn ghost" style={{ padding: "1px 6px", fontSize: 11 }} onClick={() => onOpenObjective(o.id)}>
                      view
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {id && (
        <div className="card">
          <h3>Trace — {trace?.objective.id || id}</h3>
          {err && <p className="err">{err}</p>}
          {trace && (
            <>
              <div className="row" style={{ marginBottom: 10 }}>
                <span className={chipClass(trace.objective.status)}>{trace.objective.status}</span>
                <span className="meta">{trace.objective.goal}</span>
              </div>
              <VerificationCard verification={trace.verification} tasks={trace.tasks} />
            </>
          )}
        </div>
      )}
    </div>
  );
}

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AuthoritySnapshot, DEFAULT_AUTH_BUDGETS, ObjectiveRow, RadClient, Status } from "./api";
import { apiBase, backendStop, isTauri, launchAndConnect, ConnState } from "./backend";
import { Ctx } from "./ctx";
import ActiveRun from "./pages/ActiveRun";
import Artifacts from "./pages/Artifacts";
import AuthorityPage from "./pages/Authority";
import Jerry from "./pages/Jerry";
import Memory from "./pages/Memory";
import Objectives from "./pages/Objectives";
import SettingsPage from "./pages/Settings";
import Tasks from "./pages/Tasks";
import Trace from "./pages/Trace";
import Verification from "./pages/Verification";
import { pickFocus } from "./util";

type Page =
  | "jerry"
  | "objectives"
  | "active"
  | "tasks"
  | "trace"
  | "verification"
  | "artifacts"
  | "authority"
  | "memory"
  | "settings";

const PAGES: { id: Page; label: string }[] = [
  { id: "jerry", label: "Jerry" },
  { id: "objectives", label: "Objectives" },
  { id: "active", label: "Active Run" },
  { id: "tasks", label: "Tasks" },
  { id: "trace", label: "Trace" },
  { id: "verification", label: "Verification" },
  { id: "artifacts", label: "Artifacts" },
  { id: "authority", label: "Authority" },
  { id: "memory", label: "Memory" },
  { id: "settings", label: "Settings" },
];

export default function App() {
  const [page, setPage] = useState<Page>("jerry");
  const [client, setClient] = useState<RadClient | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [auth, setAuth] = useState<AuthoritySnapshot | null>(null);
  const [backend, setBackend] = useState<ConnState>("connecting");
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [objectives, setObjectives] = useState<ObjectiveRow[]>([]);
  const manualRef = useRef(false);

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
      await launchAndConnect(connect);
    } catch (e) {
      manualRef.current = false;
      setBackend("down");
      setError(e instanceof Error ? e.message : String(e));
    }
  }, [connect]);

  useEffect(() => {
    void boot();
  }, [boot]);

  // background health poll → reconnect loop (never silent)
  const clientRef = useRef<RadClient | null>(null);
  clientRef.current = client;
  useEffect(() => {
    if (backend !== "connected") return;
    let retries = 0;
    const t = setInterval(async () => {
      const c = clientRef.current;
      if (!c) return;
      try {
        await c.health();
        retries = 0;
        const [st, a] = await Promise.all([c.status(), c.authority()]);
        setStatus(st);
        setAuth(a);
        const objs = await c.objectives(false);
        setObjectives(objs.objectives);
      } catch {
        retries += 1;
        if (retries === 1) {
          setBackend("reconnecting");
          setError("backend connection lost — reconnecting…");
        }
        if (retries >= 3) {
          retries = 0;
          try {
            await launchAndConnect(connect);
          } catch (e) {
            setBackend("down");
            setError(e instanceof Error ? e.message : String(e));
          }
        }
      }
    }, 5000);
    return () => clearInterval(t);
  }, [backend, connect]);

  const refresh = useCallback(async () => {
    const c = clientRef.current;
    if (!c) return;
    const [st, a, objs] = await Promise.all([c.status(), c.authority(), c.objectives(false)]);
    setStatus(st);
    setAuth(a);
    setObjectives(objs.objectives);
  }, []);

  useEffect(() => {
    if (client) void refresh().catch(() => {});
  }, [client]); // eslint-disable-line react-hooks/exhaustive-deps

  const shutdown = useCallback(async () => {
    try {
      await backendStop();
    } finally {
      setClient(null);
      setStatus(null);
      setAuth(null);
      setBackend("down");
      setError("backend shut down. Use “Launch / reconnect” to start it again.");
    }
  }, []);

  const selected = useMemo(
    () => objectives.find((o) => o.id === selectedId) || null,
    [objectives, selectedId],
  );

  const ctxValue = useMemo(
    () => ({
      client: client as RadClient,
      status,
      auth: (auth as AuthoritySnapshot) || {
        profile: "STANDARD",
        blurb: "",
        confirmation: "ask",
        confirmation_is_automatic: false,
        unrestricted: false,
        unrestricted_authorized: false,
        scopes: { workspace_only: true, extra_paths: [], hosts: [] },
        capabilities: {},
        policy_capabilities: {},
        passthrough: true,
        budgets: DEFAULT_AUTH_BUDGETS,
        invariants: {},
        updated: 0,
      },
      selectedId,
      selected: selected || pickFocus(objectives),
      select: setSelectedId,
      onAuth: setAuth,
      refresh,
    }),
    [client, status, auth, selectedId, selected, objectives, refresh],
  );

  const model = status?.chain?.[0] || "no brain";

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          RAD Desktop
          <span>{status?.version ? `backend v${status.version}` : "connecting"} · surface over the control plane</span>
        </div>
        <nav className="nav">
          {PAGES.map((p) => (
            <button
              key={p.id}
              className={page === p.id ? "active" : ""}
              onClick={() => setPage(p.id)}
            >
              {p.label}
              {p.id === "objectives" && objectives.length > 0 && (
                <span className="nav-count">{objectives.length}</span>
              )}
              {p.id === "active" && isRunning(selected) && <span className="dot ok nav-dot" />}
            </button>
          ))}
        </nav>
      </aside>
      <main className="main">
        {backend !== "connected" || !client || !auth ? (
          <ConnectScreen
            backend={backend}
            error={error}
            onRetry={boot}
            onManual={(base, token) => connect(base, token).catch((e) => setError(String(e)))}
          />
        ) : (
          <Ctx.Provider value={ctxValue}>
            {page === "jerry" && <Jerry />}
            {page === "objectives" && <Objectives />}
            {page === "active" && <ActiveRun />}
            {page === "tasks" && <Tasks />}
            {page === "trace" && <Trace />}
            {page === "verification" && <Verification />}
            {page === "artifacts" && <Artifacts />}
            {page === "authority" && <AuthorityPage />}
            {page === "memory" && <Memory />}
            {page === "settings" && <SettingsPage onShutdown={shutdown} />}
          </Ctx.Provider>
        )}
      </main>
      <footer className="status">
        <span>
          <i className={`dot ${backend === "connected" ? "ok" : backend === "reconnecting" ? "warn" : "off"}`} />
          {backend}
        </span>
        <span className={`pill ${auth?.profile || "STANDARD"}`}>{auth?.profile || "—"}</span>
        <span>{model}</span>
        <span>
          budget {auth?.budgets.tool_calls ?? 60} tools / {auth?.budgets.model_calls ?? 80} model
        </span>
        {selected && <span className="hint">focus: {selected.id.slice(0, 12)} ({selected.status})</span>}
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

function isRunning(o: ObjectiveRow | null): boolean {
  return o ? ["running", "planning"].includes(o.status.toLowerCase()) : false;
}

function ConnectScreen({
  backend,
  error,
  onRetry,
  onManual,
}: {
  backend: string;
  error: string;
  onRetry: () => void;
  onManual: (base: string, token: string) => void;
}) {
  const [manualBase, setManualBase] = useState(apiBase());
  const [manualToken, setManualToken] = useState("");
  const [busy, setBusy] = useState(false);

  const manualConnect = () => {
    setBusy(true);
    onManual(manualBase, manualToken);
    setTimeout(() => setBusy(false), 1500);
  };

  return (
    <div className="connect">
      <h1>Connect to RAD</h1>
      <p className="lead">
        Desktop is a surface over the existing Python API. It cannot run tools, raise budgets,
        or bypass Policy.decide.
      </p>
      {backend === "reconnecting" && <p className="warn-line">reconnecting…</p>}
      {error && <p className="err">{error}</p>}
      <div className="card">
        <button className="btn" onClick={onRetry} disabled={busy}>
          {backend === "connecting" ? "Connecting…" : "Launch / reconnect"}
        </button>
      </div>
      <div className="card">
        <label>Manual connect (existing rad serve)</label>
        <label>API base</label>
        <input value={manualBase} onChange={(e) => setManualBase(e.target.value)} />
        <label style={{ marginTop: 10 }}>Bearer token</label>
        <input
          value={manualToken}
          onChange={(e) => setManualToken(e.target.value)}
          placeholder="from <rad home>/api.token"
        />
        <div className="row" style={{ marginTop: 12 }}>
          <button className="btn ghost" onClick={manualConnect} disabled={busy || !manualToken}>
            Connect with token
          </button>
        </div>
      </div>
    </div>
  );
}

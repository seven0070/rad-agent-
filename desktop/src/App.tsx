import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AuthoritySnapshot, DEFAULT_AUTH_BUDGETS, ObjectiveRow, RadClient, Status } from "./api";
import { apiBase, backendStop, isTauri, launchAndConnect, ConnState } from "./backend";
import ChatView from "./components/ChatView";
import InspectorDrawer from "./components/InspectorDrawer";
import { Ctx } from "./ctx";
import Artifacts from "./pages/Artifacts";
import AuthorityPage from "./pages/Authority";
import Memory from "./pages/Memory";
import Ledger from "./pages/Ledger";
import Objectives from "./pages/Objectives";
import SettingsPage from "./pages/Settings";
import Tasks from "./pages/Tasks";
import Trace from "./pages/Trace";
import Verification from "./pages/Verification";
import { fmtTime, pickFocus } from "./util";

type Page =
  | "active"
  | "objectives"
  | "tasks"
  | "trace"
  | "verification"
  | "artifacts"
  | "authority"
  | "memory"
  | "ledger"
  | "settings";

const PAGES: { id: Page; label: string; icon: string }[] = [
  { id: "active", label: "Agent Session", icon: "✦" },
  { id: "objectives", label: "Objectives", icon: "☵" },
  { id: "tasks", label: "Tasks", icon: "☑" },
  { id: "trace", label: "Telemetry Trace", icon: "⚡" },
  { id: "verification", label: "Verification", icon: "🛡" },
  { id: "artifacts", label: "Artifacts", icon: "☷" },
  { id: "authority", label: "Authority", icon: "⚖" },
  { id: "memory", label: "Memory", icon: "◉" },
  { id: "ledger", label: "Replication Ledger", icon: "📜" },
  { id: "settings", label: "Settings", icon: "⚙" },
];

export default function App() {
  const [page, setPage] = useState<Page>("active");
  const [client, setClient] = useState<RadClient | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [auth, setAuth] = useState<AuthoritySnapshot | null>(null);
  const [backend, setBackend] = useState<ConnState>("connecting");
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [objectives, setObjectives] = useState<ObjectiveRow[]>([]);
  const [isInspectorOpen, setIsInspectorOpen] = useState(true);
  const [selectedArtifactId, setSelectedArtifactId] = useState<string | null>(null);
  const manualRef = useRef(false);

  const connect = useCallback(async (base: string, token: string) => {
    const c = new RadClient(base, token);
    const h = await c.health();
    if (!h.ok) throw new Error("backend not healthy");
    const [st, a, objs] = await Promise.all([
      c.status(),
      c.authority(),
      c.objectives(false).catch(() => ({ objectives: [] })),
    ]);
    setClient(c);
    setStatus(st);
    setAuth(a);
    setObjectives(objs.objectives || []);
    if (objs.objectives?.length && !selectedId) {
      setSelectedId(objs.objectives[0].id);
    }
    setBackend("connected");
    setError("");
  }, [selectedId]);

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

  // background health poll → reconnect loop
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
        const [st, a, objs] = await Promise.all([
          c.status(),
          c.authority(),
          c.objectives(false).catch(() => ({ objectives: [] })),
        ]);
        setStatus(st);
        setAuth(a);
        setObjectives(objs.objectives || []);
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
    }, 4000);
    return () => clearInterval(t);
  }, [backend, connect]);

  const refresh = useCallback(async () => {
    const c = clientRef.current;
    if (!c) return;
    const [st, a, objs] = await Promise.all([
      c.status(),
      c.authority(),
      c.objectives(false).catch(() => ({ objectives: [] })),
    ]);
    setStatus(st);
    setAuth(a);
    setObjectives(objs.objectives || []);
  }, []);

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
    () => objectives.find((o) => o.id === selectedId) || pickFocus(objectives),
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
      selectedId: selected?.id || null,
      selected,
      select: (id: string | null) => {
        setSelectedId(id);
        if (id) setPage("active");
      },
      onAuth: setAuth,
      refresh,
    }),
    [client, status, auth, selected, refresh],
  );

  const model = status?.chain?.[0] || "gemini-2.5-pro";

  return (
    <div className={`app ${isInspectorOpen ? "" : "inspector-collapsed"}`}>
      {/* 1. Left Sidebar (RAD Agent Navigation & Recent Sessions) */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="rad-logo-mark">RAD</div>
          <div className="brand-text">
            <span className="brand-title">RAD Desktop</span>
            <span className="brand-subtitle">
              <span className="live-pulse-dot" />
              {status?.version ? `v${status.version} · Engine Online` : "Connecting..."}
            </span>
          </div>
        </div>

        <button
          className="btn-new-session"
          onClick={() => {
            setSelectedId(null);
            setPage("active");
          }}
        >
          <span>＋</span>
          <span>New Objective</span>
        </button>

        <div className="nav-section-title">Views</div>
        <nav className="nav-menu">
          {PAGES.map((p) => {
            const isActive = page === p.id;
            return (
              <button
                key={p.id}
                className={`nav-item ${isActive ? "active" : ""}`}
                onClick={() => setPage(p.id)}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontSize: 13, opacity: 0.7 }}>{p.icon}</span>
                  <span>{p.label}</span>
                </div>
                {p.id === "objectives" && objectives.length > 0 && (
                  <span className="nav-badge">{objectives.length}</span>
                )}
                {p.id === "active" && isRunning(selected) && (
                  <span className="live-pulse-dot" />
                )}
              </button>
            );
          })}
        </nav>

        <div className="nav-section-title" style={{ marginTop: 6 }}>
          Recent Sessions ({objectives.length})
        </div>
        <div className="session-history-list">
          {objectives.length === 0 ? (
            <div style={{ fontSize: 11, color: "var(--text-dim)", padding: "8px 10px" }}>
              No recorded sessions yet.
            </div>
          ) : (
            objectives.slice(0, 10).map((obj) => {
              const isSel = selected?.id === obj.id;
              const isOk = obj.status === "completed";
              const isFail = obj.status === "failed";

              return (
                <div
                  key={obj.id}
                  className={`session-card ${isSel ? "selected" : ""}`}
                  onClick={() => {
                    setSelectedId(obj.id);
                    setPage("active");
                  }}
                >
                  <div className="session-card-goal">{obj.goal}</div>
                  <div className="session-card-meta">
                    <span style={{ display: "flex", alignItems: "center", gap: 5 }}>
                      <i
                        className={`dot ${
                          isOk ? "ok" : isFail ? "off" : "warn"
                        }`}
                        style={{ width: 6, height: 6 }}
                      />
                      <span>{obj.status}</span>
                    </span>
                    <span>{fmtTime(obj.created || 0)}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </aside>

      {/* 2. Center Panel (Main Chat-First Surface or Subpage) */}
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
            {page === "active" && (
              <ChatView
                objective={selected}
                onSelectObjective={(newId) => {
                  setSelectedId(newId);
                  setPage("active");
                }}
                isInspectorOpen={isInspectorOpen}
                onToggleInspector={() => setIsInspectorOpen((prev) => !prev)}
                onSelectArtifact={(artId) => setSelectedArtifactId(artId)}
              />
            )}
            {page === "objectives" && <Objectives />}
            {page === "tasks" && <Tasks />}
            {page === "trace" && <Trace />}
            {page === "verification" && <Verification />}
            {page === "artifacts" && <Artifacts />}
            {page === "authority" && <AuthorityPage />}
            {page === "memory" && <Memory />}
            {page === "ledger" && <Ledger />}
            {page === "settings" && <SettingsPage onShutdown={shutdown} />}
          </Ctx.Provider>
        )}
      </main>

      {/* 3. Right Panel (Hermes Inspector Drawer) */}
      {backend === "connected" && client && auth && isInspectorOpen && (
        <Ctx.Provider value={ctxValue}>
          <InspectorDrawer
            objective={selected}
            selectedArtifactId={selectedArtifactId}
            onSelectArtifact={setSelectedArtifactId}
            onClose={() => setIsInspectorOpen(false)}
          />
        </Ctx.Provider>
      )}

      {/* 4. Bottom Telemetry Bar */}
      <footer className="status">
        <div className="status-left">
          <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <i
              className={`dot ${
                backend === "connected" ? "ok" : backend === "reconnecting" ? "warn" : "off"
              }`}
            />
            <span>{backend}</span>
          </span>
          <span className={`pill ${auth?.profile || "STANDARD"}`}>
            {auth?.profile || "STANDARD"}
          </span>
          <span style={{ color: "var(--text-secondary)" }}>{model}</span>
          <span>
            budget {auth?.budgets.tool_calls ?? 60} tools / {auth?.budgets.model_calls ?? 80} model
          </span>
          {selected && (
            <span style={{ color: "var(--text-dim)", fontFamily: "monospace", fontSize: 11 }}>
              focus: {selected.id.slice(0, 12)} ({selected.status})
            </span>
          )}
        </div>

        <div className="status-right">
          <button
            className="btn ghost mini"
            onClick={() => setIsInspectorOpen((prev) => !prev)}
            style={{ fontSize: 11, padding: "2px 8px" }}
          >
            {isInspectorOpen ? "Hide Inspector ◨" : "Show Inspector ◧"}
          </button>
          {isTauri() && (
            <button
              className="btn ghost mini"
              style={{ padding: "2px 8px", color: "var(--rose-danger)" }}
              onClick={() => void shutdown()}
            >
              shut down
            </button>
          )}
        </div>
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
    <div className="connect" style={{ maxWidth: 500, margin: "auto", padding: 32 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, margin: "0 0 8px" }}>Connect to RAD</h1>
      <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 20 }}>
        Desktop is a surface over the existing Python API. It cannot run tools, raise budgets,
        or bypass Policy.decide.
      </p>
      {backend === "reconnecting" && <p style={{ color: "var(--hermes-amber)" }}>reconnecting…</p>}
      {error && <p style={{ color: "var(--rose-danger)", fontSize: 12 }}>{error}</p>}
      <div className="card">
        <button className="btn" onClick={onRetry} disabled={busy} style={{ width: "100%" }}>
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
          <button
            className="btn ghost"
            onClick={manualConnect}
            disabled={busy || !manualToken}
            style={{ width: "100%" }}
          >
            Connect with token
          </button>
        </div>
      </div>
    </div>
  );
}

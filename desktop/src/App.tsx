import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { AuthoritySnapshot, DEFAULT_AUTH_BUDGETS, ObjectiveRow, RadClient, Status } from "./api";
import { apiBase, backendStop, isTauri, launchAndConnect, ConnState, getStoredConnection, saveStoredConnection } from "./backend";
import ChatView from "./components/ChatView";
import InspectorDrawer from "./components/InspectorDrawer";
import { WebConnectionModal } from "./components/WebConnectionModal";
import { ErrorBoundary } from "./components/ErrorBoundary";
import {
  IconSession,
  IconObjectives,
  IconTasks,
  IconTrace,
  IconVerification,
  IconArtifacts,
  IconAuthority,
  IconMemory,
  IconLedger,
  IconVitals,
  IconSettings,
} from "./components/Icons";
import { Ctx } from "./ctx";
import Artifacts from "./pages/Artifacts";
import AuthorityPage from "./pages/Authority";
import Memory from "./pages/Memory";
import Ledger from "./pages/Ledger";
import Vitals from "./pages/Vitals";
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
  | "vitals"
  | "settings";

const PRIMARY_PAGES: { id: Page; label: string; icon: ReactNode }[] = [
  { id: "active", label: "Studio Canvas", icon: <IconSession size={14} /> },
  { id: "objectives", label: "Runs & DAGs", icon: <IconObjectives size={14} /> },
  { id: "ledger", label: "Replication Ledger", icon: <IconLedger size={14} /> },
  { id: "vitals", label: "Organ Vitals", icon: <IconVitals size={14} /> },
];

const INSPECT_PAGES: { id: Page; label: string; icon: ReactNode }[] = [
  { id: "artifacts", label: "Artifacts", icon: <IconArtifacts size={14} /> },
  { id: "verification", label: "Verification", icon: <IconVerification size={14} /> },
  { id: "trace", label: "Trace", icon: <IconTrace size={14} /> },
  { id: "tasks", label: "Tasks DAG", icon: <IconTasks size={14} /> },
  { id: "authority", label: "Authority", icon: <IconAuthority size={14} /> },
  { id: "memory", label: "Memory", icon: <IconMemory size={14} /> },
  { id: "settings", label: "Settings", icon: <IconSettings size={14} /> },
];

const ALL_PAGES = [...PRIMARY_PAGES, ...INSPECT_PAGES];

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
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedNodeType, setSelectedNodeType] = useState<"objective" | "task" | "verification" | null>(null);
  const [isWebModalOpen, setIsWebModalOpen] = useState(false);
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
    setSelectedId((prev) => prev || (objs.objectives?.length ? objs.objectives[0].id : null));
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
      {/* 1. Left Sidebar (RAD Studio v2 Navigation & Recent Sessions) */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="rad-logo-mark raised">
            RAD
          </div>
          <div className="brand-text">
            <div className="flex-mid gap-6">
              <span className="brand-title">RAD Studio</span>
              <span className="badge-platform muted-plate">
                v2
              </span>
            </div>
            <span className="brand-subtitle">
              <span className="live-pulse-dot" />
              {status?.version ? `v${status.version} · Studio Online` : "Connecting..."}
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

        <div className="nav-section-title">Workspaces</div>
        <nav className="nav-menu" aria-label="Primary workspaces">
          {PRIMARY_PAGES.map((p) => {
            const isActive = page === p.id;
            return (
              <button
                key={p.id}
                className={`nav-item ${isActive ? "active" : ""}`}
                onClick={() => setPage(p.id)}
                aria-current={isActive ? "page" : undefined}
              >
                <div className="flex-mid gap-9">
                  <span
                    className={`nav-icon ${isActive ? "is-active" : ""}`}
                  >
                    {p.icon}
                  </span>
                  <span>{p.label}</span>
                </div>
                {p.id === "objectives" && objectives.length > 0 && (
                  <span className="nav-badge font-mono tabular-nums">{objectives.length}</span>
                )}
                {p.id === "active" && isRunning(selected) && (
                  <span className="live-pulse-dot" />
                )}
              </button>
            );
          })}
        </nav>

        <div className="nav-section-title mt-8">
          Deep Inspection
        </div>
        <nav className="nav-menu" aria-label="Deep inspection views">
          {INSPECT_PAGES.map((p) => {
            const isActive = page === p.id;
            return (
              <button
                key={p.id}
                className={`nav-item fs-12 ${isActive ? "active" : ""}`}
                onClick={() => setPage(p.id)}
                aria-current={isActive ? "page" : undefined}
              >
                <div className="flex-mid gap-9">
                  <span
                    className={`nav-icon ${isActive ? "is-active-dim" : ""}`}
                  >
                    {p.icon}
                  </span>
                  <span>{p.label}</span>
                </div>
              </button>
            );
          })}
        </nav>

        <div className="nav-section-title mt-6">
          Recent Sessions ({objectives.length})
        </div>
        <div className="session-history-list">
          {objectives.length === 0 ? (
            <div className="session-empty">
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
                    <span className="inline-mid gap-5">
                      <i
                        className={`dot ${
                          isOk ? "ok" : isFail ? "off" : "warn"
                        } dot-6`}
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
            <ErrorBoundary
              key={page}
              fallbackTitle={`Error Rendering ${ALL_PAGES.find((p) => p.id === page)?.label || "Surface"}`}
            >
              {page === "active" && (
                <ChatView
                  objective={selected}
                  onSelectObjective={(newId) => {
                    setSelectedId(newId);
                    setSelectedNodeId(null);
                    setSelectedNodeType(null);
                    setPage("active");
                  }}
                  isInspectorOpen={isInspectorOpen}
                  onToggleInspector={() => setIsInspectorOpen((prev) => !prev)}
                  onSelectArtifact={(artId) => setSelectedArtifactId(artId)}
                  selectedNodeId={selectedNodeId}
                  onSelectNode={(nodeId, nodeType) => {
                    setSelectedNodeId(nodeId);
                    setSelectedNodeType(nodeType);
                  }}
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
              {page === "vitals" && <Vitals />}
              {page === "settings" && <SettingsPage onShutdown={shutdown} />}
            </ErrorBoundary>
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
            selectedNodeId={selectedNodeId}
            selectedNodeType={selectedNodeType}
            onClose={() => setIsInspectorOpen(false)}
          />
        </Ctx.Provider>
      )}

      {/* 4. Bottom Telemetry Bar */}
      <footer className="status">
        <div className="status-left">
          <span className="inline-mid gap-6">
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
          <span className="tc-secondary">{model}</span>
          <span>
            budget {auth?.budgets.tool_calls ?? 60} tools / {auth?.budgets.model_calls ?? 80} model
          </span>
          {selected && (
            <span className="status-focus">
              focus: {selected.id.slice(0, 12)} ({selected.status})
            </span>
          )}
        </div>

        <div className="status-right">
          <button
            className="btn ghost mini font-mono fs-11 pad-2-8"
            onClick={() => setIsWebModalOpen(true)}
            title="Configure connection"
          >
            🌐 {isTauri() ? "Tauri" : "Web UI"}
          </button>
          <button
            className="btn ghost mini fs-11 pad-2-8"
            onClick={() => setIsInspectorOpen((prev) => !prev)}
          >
            {isInspectorOpen ? "Hide Inspector ◨" : "Show Inspector ◧"}
          </button>
          {isTauri() && (
            <button
              className="btn ghost mini pad-2-8 tc-danger"
              onClick={() => void shutdown()}
            >
              shut down
            </button>
          )}
        </div>
      </footer>

      <WebConnectionModal
        isOpen={isWebModalOpen}
        onClose={() => setIsWebModalOpen(false)}
        onConnect={async (b, t) => {
          await connect(b, t);
          setError("");
        }}
        currentBase={client?.base}
        currentToken={client?.token}
      />
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
  const stored = getStoredConnection();
  const [manualBase, setManualBase] = useState(stored.base || apiBase());
  const [manualToken, setManualToken] = useState(stored.token || "");
  const [busy, setBusy] = useState(false);

  const manualConnect = () => {
    setBusy(true);
    saveStoredConnection(manualBase, manualToken);
    onManual(manualBase, manualToken);
    setTimeout(() => setBusy(false), 1500);
  };

  return (
    <div className="connect narrow">
      <div className="flex-mid gap-10 mb-8">
        <h1 className="connect-title">
          {isTauri() ? "Connect to RAD Desktop" : "RAD Web UI Connection"}
        </h1>
        <span className="badge-platform">{isTauri() ? "TAURI" : "RUST + JS"}</span>
      </div>
      <p className="connect-lede">
        {isTauri()
          ? "Desktop is a surface over the existing Python API."
          : "Web browser frontend communicating with the RAD Agent control plane via Rust proxy or loopback API."}
      </p>
      {backend === "reconnecting" && <p className="tc-amber">reconnecting…</p>}
      {error && <p className="tc-danger fs-12">{error}</p>}
      <div className="card">
        <button className="btn w-full" onClick={onRetry} disabled={busy}>
          {backend === "connecting" ? "Connecting…" : "Launch / Reconnect"}
        </button>
      </div>
      <div className="card">
        <label>Manual connection (running `rad serve` or Rust daemon)</label>
        <label className="mt-8">API base URL</label>
        <input
          className="field-input font-mono"
          value={manualBase}
          onChange={(e) => setManualBase(e.target.value)}
          placeholder="http://127.0.0.1:7331"
        />
        <label className="mt-10">Bearer token</label>
        <input
          type="password"
          className="field-input font-mono"
          value={manualToken}
          onChange={(e) => setManualToken(e.target.value)}
          placeholder="from ~/.rad/api.token"
        />
        <div className="field-hint">
          Token is generated at <code>~/.rad/api.token</code> or logged by <code>rad serve</code>.
        </div>
        <div className="row mt-14">
          <button
            className="btn ghost w-full"
            onClick={manualConnect}
            disabled={busy || !manualToken}
          >
            Save & Connect
          </button>
        </div>
      </div>
    </div>
  );
}

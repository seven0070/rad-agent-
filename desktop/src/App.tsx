import { useCallback, useEffect, useState } from "react";
import { ApiError, AuthoritySnapshot, ObjectiveRow, RadClient, Status, TaskRow } from "./api";
import { apiBase, apiToken, backendInfo, backendStart, backendStop, isTauri } from "./backend";

export default function App() {
  const [client, setClient] = useState<RadClient | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [auth, setAuth] = useState<AuthoritySnapshot | null>(null);
  const [backend, setBackend] = useState<"connected" | "connecting" | "down">("connecting");
  const [error, setError] = useState("");
  const [manualBase, setManualBase] = useState(apiBase());
  const [manualToken, setManualToken] = useState("");

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
        try {
          await backendStart(info.port || 7331);
        } catch {
          /* may already be running externally */
        }
        const token = await apiToken();
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
      setStatus(null);
      setAuth(null);
      setBackend("down");
    }
  }, []);

  const model = status?.chain?.[0] || "no brain";

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="eyebrow">RAD Desktop 0.1</div>
          <h1>Minimal app layer</h1>
        </div>
        <div className="topbar-actions">
          <span>
            <i className={`dot ${backend === "connected" ? "ok" : "off"}`} />
            {backend === "connected" ? "backend connected" : backend}
          </span>
          <span className={`pill ${auth?.profile || "STANDARD"}`}>{auth?.profile || "—"}</span>
          <button className="btn ghost" onClick={() => void boot()}>
            Reconnect
          </button>
          {isTauri() && backend === "connected" && (
            <button className="btn ghost" onClick={() => void shutdown()}>
              Shut down
            </button>
          )}
        </div>
      </header>

      <main className="main simple-main">
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
          <Dashboard client={client} auth={auth} status={status} model={model} onRefresh={refresh} />
        )}
      </main>
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
    <div className="connect minimal-width">
      <h2>Connect to RAD</h2>
      <p className="lead">
        This desktop app is only a small surface over the existing Python API. Tools still run in the
        backend control plane.
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
        <label style={{ marginTop: 10 }}>API token</label>
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

function Dashboard(props: {
  client: RadClient;
  auth: AuthoritySnapshot;
  status: Status | null;
  model: string;
  onRefresh: () => Promise<void>;
}) {
  const [objectives, setObjectives] = useState<ObjectiveRow[]>([]);
  const [tasks, setTasks] = useState<TaskRow[]>([]);
  const [feedError, setFeedError] = useState("");

  const load = useCallback(async () => {
    setFeedError("");
    try {
      const [objectiveData, taskData] = await Promise.all([
        props.client.objectives(true),
        props.client.tasks(),
        props.onRefresh(),
      ]);
      setObjectives(objectiveData.objectives);
      setTasks(taskData.tasks);
    } catch (e) {
      setFeedError(e instanceof Error ? e.message : String(e));
    }
  }, [props]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="dashboard">
      <section className="hero card">
        <div>
          <div className="eyebrow">Surface over rad serve</div>
          <h2>Minimal desktop view for chat, objectives, and task status.</h2>
        </div>
        <div className="hero-grid">
          <Metric label="Profile" value={props.auth.profile} />
          <Metric label="Model" value={props.model} />
          <Metric
            label="Objective summary"
            value={`${props.status?.objectives?.total ?? 0} total · ${props.status?.objectives?.open_tasks ?? 0} open tasks`}
          />
          <Metric
            label="Budget"
            value={`${props.auth.budgets.tool_calls} tools · ${props.auth.budgets.model_calls} model`}
          />
        </div>
        <div className="row">
          <button className="btn ghost" onClick={() => void load()}>
            Refresh
          </button>
          <span className="lead compact">{props.auth.blurb}</span>
        </div>
        {feedError && <p className="err">{feedError}</p>}
      </section>

      <section className="dashboard-grid">
        <ChatCard client={props.client} />
        <ObjectivesCard client={props.client} objectives={objectives} onCreated={load} />
      </section>

      <section className="dashboard-grid secondary">
        <ListCard
          title="Recent objectives"
          empty="No active objectives"
          items={objectives.slice(0, 6).map((objective) => ({
            key: objective.id,
            title: objective.goal,
            meta: `${objective.status} · ${objective.verification || "unverified"}`,
          }))}
        />
        <ListCard
          title="Recent tasks"
          empty="No tasks yet"
          items={tasks.slice(0, 8).map((task) => ({
            key: `${task.objective_id || "root"}-${task.id}`,
            title: task.title || task.text || task.id,
            meta: `${task.status} · ${task.verification?.status || "unverified"}`,
          }))}
        />
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ChatCard({ client }: { client: RadClient }) {
  const [text, setText] = useState("");
  const [messages, setMessages] = useState<Array<{ who: "user" | "rad"; text: string }>>([]);
  const [busy, setBusy] = useState(false);

  const send = async () => {
    const trimmed = text.trim();
    if (!trimmed || busy) return;
    setText("");
    setMessages((current) => [...current, { who: "user", text: trimmed }]);
    setBusy(true);
    try {
      const reply = await client.chat(trimmed);
      setMessages((current) => [...current, { who: "rad", text: reply.reply }]);
    } catch (e) {
      setMessages((current) => [
        ...current,
        { who: "rad", text: e instanceof Error ? e.message : String(e) },
      ]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card panel">
      <h2>Chat</h2>
      <p className="lead">Send a message to the existing RAD backend.</p>
      <div className="msgs compact-feed">
        {messages.length === 0 && (
          <div className="bubble rad">Messages stay in the existing backend session.</div>
        )}
        {messages.map((message, index) => (
          <div key={`${message.who}-${index}`} className={`bubble ${message.who}`}>
            {message.text}
          </div>
        ))}
      </div>
      <div className="row stack-mobile">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void send();
            }
          }}
          placeholder="Message RAD…"
        />
        <button className="btn" disabled={busy} onClick={() => void send()}>
          {busy ? "Sending…" : "Send"}
        </button>
      </div>
    </div>
  );
}

function ObjectivesCard(props: {
  client: RadClient;
  objectives: ObjectiveRow[];
  onCreated: () => Promise<void>;
}) {
  const [goal, setGoal] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  const create = async () => {
    const trimmed = goal.trim();
    if (!trimmed || creating) return;
    setCreating(true);
    setError("");
    setMessage("");
    try {
      const created = await props.client.createObjective(trimmed);
      setGoal("");
      setMessage(created.note || (created.started ? "Objective started" : "Objective created"));
      await props.onCreated();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="card panel">
      <h2>Objectives</h2>
      <p className="lead">Create a new objective and watch the active queue.</p>
      <label>New objective</label>
      <input value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="Ship a minimal desktop layer" />
      <div className="row" style={{ marginTop: 12 }}>
        <button className="btn" disabled={creating} onClick={() => void create()}>
          {creating ? "Creating…" : "Create"}
        </button>
      </div>
      {error && <p className="err">{error}</p>}
      {message && <p className="ok">{message}</p>}
      <div className="mini-list">
        {props.objectives.slice(0, 5).map((objective) => (
          <div key={objective.id} className="mini-item">
            <strong>{objective.goal}</strong>
            <span>{objective.status}</span>
          </div>
        ))}
        {props.objectives.length === 0 && <p className="lead compact">No active objectives</p>}
      </div>
    </div>
  );
}

function ListCard(props: {
  title: string;
  empty: string;
  items: Array<{ key: string; title: string; meta: string }>;
}) {
  return (
    <div className="card panel">
      <h2>{props.title}</h2>
      <div className="mini-list">
        {props.items.length === 0 && <p className="lead compact">{props.empty}</p>}
        {props.items.map((item) => (
          <div key={item.key} className="mini-item">
            <strong>{item.title}</strong>
            <span>{item.meta}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

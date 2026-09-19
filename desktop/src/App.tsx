import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, AuthoritySnapshot, ObjectiveRow, RadClient, Status, TaskRow } from "./api";
import { apiBase, apiToken, backendInfo, backendStart, backendStop, isTauri } from "./backend";

type Page = "overview" | "assistant" | "objectives" | "tasks";

type NavItem = {
  id: Page;
  label: string;
  hint: string;
};

const NAV_ITEMS: NavItem[] = [
  { id: "overview", label: "Overview", hint: "Status and summaries" },
  { id: "assistant", label: "Assistant", hint: "Chat with RAD" },
  { id: "objectives", label: "Objectives", hint: "Create and inspect work" },
  { id: "tasks", label: "Tasks", hint: "Track execution" },
];

export default function App() {
  const [page, setPage] = useState<Page>("overview");
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

  const waitForToken = useCallback(async () => {
    let last = "";
    for (let i = 0; i < 40; i += 1) {
      try {
        const token = await apiToken();
        if (token) return token;
      } catch (e) {
        last = e instanceof Error ? e.message : String(e);
      }
      await new Promise((resolve) => window.setTimeout(resolve, 250));
    }
    throw new Error(last || "RAD API token was not created in time");
  }, []);

  const boot = useCallback(async () => {
    setBackend("connecting");
    setError("");
    try {
      if (isTauri()) {
        const info = await backendInfo();
        let startError = "";
        try {
          await backendStart(info.port || 7331);
        } catch (e) {
          startError = e instanceof Error ? e.message : String(e);
        }
        const token = await waitForToken();
        if (!token) throw new Error(startError || "no API token — desktop could not start the bundled backend");
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
  }, [connect, waitForToken]);

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
    <div className="shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="eyebrow">RAD Desktop</div>
          <h1>Operator Console</h1>
          <p className="lead compact">Organized surface over the existing RAD backend.</p>
        </div>

        <nav className="nav-list">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${page === item.id ? "active" : ""}`}
              onClick={() => setPage(item.id)}
            >
              <strong>{item.label}</strong>
              <span>{item.hint}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-card">
          <span className="muted-label">Connection</span>
          <div className="status-line">
            <i className={`dot ${backend === "connected" ? "ok" : "off"}`} />
            {backend === "connected" ? "Backend connected" : backend}
          </div>
          <div className="sidebar-meta">
            <span className={`pill ${auth?.profile || "STANDARD"}`}>{auth?.profile || "—"}</span>
            <span>{model}</span>
          </div>
          <div className="sidebar-actions">
            <button className="btn ghost" onClick={() => void boot()}>
              Reconnect
            </button>
            {isTauri() && backend === "connected" && (
              <button className="btn ghost" onClick={() => void shutdown()}>
                Shut down
              </button>
            )}
          </div>
        </div>
      </aside>

      <main className="workspace">
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
          <Workspace
            page={page}
            client={client}
            auth={auth}
            model={model}
            status={status}
            onRefresh={refresh}
          />
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
    <div className="connect-screen">
      <div className="page-header">
        <div>
          <div className="eyebrow">Connect</div>
          <h2>Attach the desktop app to RAD</h2>
        </div>
      </div>

      <div className="content-grid single">
        <section className="card">
          <p className="lead">
            This desktop app can launch its own bundled RAD backend. Tools, plans, and execution still
            continue in the Python control plane behind <code>rad serve</code>.
          </p>
          {props.error && <p className="err">{props.error}</p>}
          <div className="sidebar-actions">
            <button className="btn" onClick={props.onRetry}>
              {props.backend === "connecting" ? "Connecting…" : "Launch / reconnect"}
            </button>
          </div>
        </section>

        <section className="card">
          <label>API base</label>
          <input value={props.manualBase} onChange={(e) => props.setManualBase(e.target.value)} />
          <label style={{ marginTop: 12 }}>API token</label>
          <input
            value={props.manualToken}
            onChange={(e) => props.setManualToken(e.target.value)}
            placeholder="from ~/.rad/api.token"
          />
          <div className="sidebar-actions" style={{ marginTop: 16 }}>
            <button className="btn ghost" onClick={props.onManual}>
              Connect with token
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}

function Workspace(props: {
  page: Page;
  client: RadClient;
  auth: AuthoritySnapshot;
  status: Status | null;
  model: string;
  onRefresh: () => Promise<void>;
}) {
  const [objectives, setObjectives] = useState<ObjectiveRow[]>([]);
  const [tasks, setTasks] = useState<TaskRow[]>([]);
  const [selectedObjectiveId, setSelectedObjectiveId] = useState<string>("");
  const [feedError, setFeedError] = useState("");

  const load = useCallback(async () => {
    setFeedError("");
    try {
      const [objectiveData, taskData] = await Promise.all([
        props.client.objectives(),
        props.client.tasks(),
        props.onRefresh(),
      ]);
      setObjectives(objectiveData.objectives);
      setTasks(taskData.tasks);
      setSelectedObjectiveId((current) => current || objectiveData.objectives[0]?.id || "");
    } catch (e) {
      setFeedError(e instanceof Error ? e.message : String(e));
    }
  }, [props.client, props.onRefresh]);

  useEffect(() => {
    void load();
  }, [load]);

  const selectedObjective = useMemo(
    () => objectives.find((objective) => objective.id === selectedObjectiveId) || objectives[0] || null,
    [objectives, selectedObjectiveId],
  );

  const pageMeta = PAGE_META[props.page];

  return (
    <div className="workspace-body">
      <header className="page-header">
        <div>
          <div className="eyebrow">{pageMeta.eyebrow}</div>
          <h2>{pageMeta.title}</h2>
        </div>
        <div className="page-actions">
          <span className="meta-chip">{props.auth.profile}</span>
          <span className="meta-chip">{props.model}</span>
          <button className="btn ghost" onClick={() => void load()}>
            Refresh
          </button>
        </div>
      </header>

      {feedError && <p className="err">{feedError}</p>}

      {props.page === "overview" && (
        <OverviewPage auth={props.auth} status={props.status} objectives={objectives} tasks={tasks} />
      )}
      {props.page === "assistant" && <AssistantPage client={props.client} auth={props.auth} />}
      {props.page === "objectives" && (
        <ObjectivesPage
          client={props.client}
          objectives={objectives}
          selectedObjectiveId={selectedObjective?.id || ""}
          onSelect={setSelectedObjectiveId}
          onCreated={load}
        />
      )}
      {props.page === "tasks" && <TasksPage tasks={tasks} objectives={objectives} />}
    </div>
  );
}

const PAGE_META: Record<Page, { eyebrow: string; title: string }> = {
  overview: { eyebrow: "Command center", title: "System overview" },
  assistant: { eyebrow: "Assistant", title: "Chat with RAD" },
  objectives: { eyebrow: "Planner", title: "Objectives and queue" },
  tasks: { eyebrow: "Executor", title: "Task board" },
};

function OverviewPage(props: {
  auth: AuthoritySnapshot;
  status: Status | null;
  objectives: ObjectiveRow[];
  tasks: TaskRow[];
}) {
  const openTasks = props.status?.objectives?.open_tasks ?? props.tasks.filter((task) => task.status !== "DONE").length;
  const activeObjectives = props.objectives.filter((objective) => objective.status !== "DONE").length;
  const pendingTasks = props.tasks.filter((task) => task.status === "PENDING" || task.status === "READY").length;

  return (
    <div className="page-stack">
      <section className="hero card">
        <div>
          <div className="eyebrow">Surface over rad serve</div>
          <h3>Organized desktop shell for monitoring the agent, chatting, and managing queued work.</h3>
        </div>
        <div className="stats-grid">
          <Metric label="Authority" value={props.auth.profile} />
          <Metric label="Objectives" value={`${activeObjectives} active`} />
          <Metric label="Open tasks" value={`${openTasks}`} />
          <Metric label="Pending / ready" value={`${pendingTasks}`} />
        </div>
        <p className="lead compact">{props.auth.blurb}</p>
      </section>

      <div className="content-grid">
        <section className="card panel">
          <h3>Recent objectives</h3>
          <ListCard
            empty="No objectives yet"
            items={props.objectives.slice(0, 5).map((objective) => ({
              key: objective.id,
              title: objective.goal,
              meta: `${objective.status} · ${objective.verification || "unverified"}`,
            }))}
          />
        </section>
        <section className="card panel">
          <h3>Execution snapshot</h3>
          <ListCard
            empty="No tasks yet"
            items={props.tasks.slice(0, 6).map((task) => ({
              key: `${task.objective_id || "root"}-${task.id}`,
              title: task.title || task.text || task.id,
              meta: `${task.status} · ${task.verification?.status || "unverified"}`,
            }))}
          />
        </section>
      </div>
    </div>
  );
}

function AssistantPage(props: { client: RadClient; auth: AuthoritySnapshot }) {
  return (
    <div className="content-grid assistant-layout">
      <ChatPanel client={props.client} />
      <section className="card panel side-panel">
        <h3>Operator notes</h3>
        <p className="lead">
          Messages stay routed through the existing backend session. This UI does not bypass policy, tools,
          or authority checks.
        </p>
        <div className="mini-list">
          <div className="mini-item block">
            <strong>Authority</strong>
            <span>{props.auth.profile}</span>
          </div>
          <div className="mini-item block">
            <strong>Confirmation</strong>
            <span>{props.auth.confirmation}</span>
          </div>
          <div className="mini-item block">
            <strong>Budget</strong>
            <span>
              {props.auth.budgets.tool_calls} tools · {props.auth.budgets.model_calls} model · {props.auth.budgets.retries} retries
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}

function ObjectivesPage(props: {
  client: RadClient;
  objectives: ObjectiveRow[];
  selectedObjectiveId: string;
  onSelect: (id: string) => void;
  onCreated: () => Promise<void>;
}) {
  const [goal, setGoal] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);

  const selectedObjective = props.objectives.find((objective) => objective.id === props.selectedObjectiveId) || null;

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
      props.onSelect(created.id);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="content-grid">
      <section className="card panel">
        <h3>Create objective</h3>
        <p className="lead">Add work to the planner while keeping execution in the backend control plane.</p>
        <label>Objective</label>
        <input value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="Ship an organized desktop surface" />
        <div className="sidebar-actions" style={{ marginTop: 16 }}>
          <button className="btn" disabled={creating} onClick={() => void create()}>
            {creating ? "Creating…" : "Create objective"}
          </button>
        </div>
        {error && <p className="err">{error}</p>}
        {message && <p className="ok">{message}</p>}
      </section>

      <section className="card panel">
        <h3>Objective list</h3>
        <div className="mini-list selectable-list">
          {props.objectives.length === 0 && <p className="lead compact">No objectives yet</p>}
          {props.objectives.map((objective) => (
            <button
              key={objective.id}
              className={`mini-item selectable ${props.selectedObjectiveId === objective.id ? "active" : ""}`}
              onClick={() => props.onSelect(objective.id)}
            >
              <strong>{objective.goal}</strong>
              <span>{objective.status}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="card panel full-width">
        <h3>Selected objective</h3>
        {selectedObjective ? (
          <div className="detail-grid">
            <Metric label="Goal" value={selectedObjective.goal} />
            <Metric label="Status" value={selectedObjective.status} />
            <Metric label="Verification" value={selectedObjective.verification || "—"} />
            <Metric label="ID" value={selectedObjective.id.slice(0, 12)} />
          </div>
        ) : (
          <p className="lead compact">Select an objective to inspect it.</p>
        )}
      </section>
    </div>
  );
}

function TasksPage(props: { tasks: TaskRow[]; objectives: ObjectiveRow[] }) {
  const groups = useMemo(() => {
    return [
      {
        title: "Ready / pending",
        items: props.tasks.filter((task) => task.status === "READY" || task.status === "PENDING"),
      },
      {
        title: "Running / blocked",
        items: props.tasks.filter((task) => task.status === "RUNNING" || task.status === "BLOCKED"),
      },
      {
        title: "Completed",
        items: props.tasks.filter((task) => task.status === "DONE" || task.status === "VERIFIED"),
      },
    ];
  }, [props.tasks]);

  return (
    <div className="page-stack">
      <section className="card hero">
        <div>
          <div className="eyebrow">Execution board</div>
          <h3>
            {props.tasks.length} tasks across {props.objectives.length} objectives
          </h3>
        </div>
        <p className="lead compact">Track what is queued, active, blocked, and complete from one place.</p>
      </section>

      <div className="content-grid triple">
        {groups.map((group) => (
          <section key={group.title} className="card panel">
            <h3>{group.title}</h3>
            <ListCard
              empty="Nothing here"
              items={group.items.slice(0, 8).map((task) => ({
                key: `${task.objective_id || "root"}-${task.id}`,
                title: task.title || task.text || task.id,
                meta: `${task.status} · ${task.verification?.status || "unverified"}`,
              }))}
            />
          </section>
        ))}
      </div>
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

function ChatPanel({ client }: { client: RadClient }) {
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
    <section className="card panel chat-panel">
      <h3>Conversation</h3>
      <p className="lead">Send messages to the existing RAD session through the HTTP API.</p>
      <div className="msgs transcript">
        {messages.length === 0 && (
          <div className="bubble rad">Messages stay in the backend session and follow existing policy.</div>
        )}
        {messages.map((message, index) => (
          <div key={`${message.who}-${index}`} className={`bubble ${message.who}`}>
            {message.text}
          </div>
        ))}
      </div>
      <div className="composer">
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
    </section>
  );
}

function ListCard(props: { empty: string; items: Array<{ key: string; title: string; meta: string }> }) {
  return (
    <div className="mini-list">
      {props.items.length === 0 && <p className="lead compact">{props.empty}</p>}
      {props.items.map((item) => (
        <div key={item.key} className="mini-item block">
          <strong>{item.title}</strong>
          <span>{item.meta}</span>
        </div>
      ))}
    </div>
  );
}

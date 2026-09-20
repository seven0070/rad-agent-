import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  ApiError,
  ArtifactRow,
  AuthoritySnapshot,
  EventRow,
  ObjectiveRow,
  ObservationRow,
  Profile,
  RadClient,
  Settings,
  Status,
  TaskRow,
  verifyLabel,
} from "./api";
import {
  apiBase,
  apiToken,
  backendInfo,
  backendStart,
  backendStop,
  isTauri,
} from "./backend";

type Page =
  | "chat"
  | "objectives"
  | "execution"
  | "graph"
  | "trace"
  | "verification"
  | "artifacts"
  | "provenance"
  | "usage"
  | "permissions"
  | "settings";

const PAGES: { id: Page; label: string }[] = [
  { id: "chat", label: "Jerry" },
  { id: "objectives", label: "Objectives" },
  { id: "execution", label: "Execution" },
  { id: "graph", label: "Task graph" },
  { id: "trace", label: "Trace" },
  { id: "verification", label: "Verification" },
  { id: "artifacts", label: "Artifacts" },
  { id: "provenance", label: "Why" },
  { id: "usage", label: "Usage" },
  { id: "permissions", label: "Permissions" },
  { id: "settings", label: "Settings" },
];

const HINTS = [
  "Build a small Flask API.",
  "Research this topic and produce a report.",
  "Write three facts about RAD to facts.md, then summarise into summary.txt",
  "Continue the previous objective.",
];

export default function App() {
  const [page, setPage] = useState<Page>("chat");
  const [client, setClient] = useState<RadClient | null>(null);
  const [status, setStatus] = useState<Status | null>(null);
  const [auth, setAuth] = useState<AuthoritySnapshot | null>(null);
  const [backend, setBackend] = useState<"connected" | "connecting" | "down">("connecting");
  const [error, setError] = useState("");
  const [manualBase, setManualBase] = useState(apiBase());
  const [manualToken, setManualToken] = useState("");
  const [selectedId, setSelectedId] = useState("");
  const [objectives, setObjectives] = useState<ObjectiveRow[]>([]);

  const connect = useCallback(async (base: string, token: string) => {
    const c = new RadClient(base, token);
    const h = await c.health();
    if (!h.ok) throw new Error("backend not healthy");
    const [st, a, o] = await Promise.all([c.status(), c.authority(), c.objectives()]);
    setClient(c);
    setStatus(st);
    setAuth(a);
    setObjectives(o.objectives);
    if (!selectedId && o.objectives[0]) setSelectedId(o.objectives[0].id);
    setBackend("connected");
    setError("");
  }, [selectedId]);

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
    const [st, a, o] = await Promise.all([client.status(), client.authority(), client.objectives()]);
    setStatus(st);
    setAuth(a);
    setObjectives(o.objectives);
    if (selectedId && !o.objectives.some((x) => x.id === selectedId) && o.objectives[0]) {
      setSelectedId(o.objectives[0].id);
    }
    if (!selectedId && o.objectives[0]) setSelectedId(o.objectives[0].id);
  }, [client, selectedId]);

  useEffect(() => {
    if (!client) return;
    const live = objectives.some((o) => o.status === "running" || o.status === "planning");
    const t = window.setInterval(() => void refresh(), live ? 1200 : 4000);
    return () => window.clearInterval(t);
  }, [client, objectives, refresh]);

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
          <span>1.0.1 · operator surface</span>
        </div>
        <nav className="nav">
          {PAGES.map((p) => (
            <button key={p.id} className={page === p.id ? "active" : ""} onClick={() => setPage(p.id)}>
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
            objectives={objectives}
            selectedId={selectedId}
            setSelectedId={setSelectedId}
            onAuth={setAuth}
            onRefresh={refresh}
            go={(p, id) => {
              if (id) setSelectedId(id);
              setPage(p);
            }}
          />
        )}
      </main>
      <footer className="status">
        <span>
          <i className={`dot ${backend === "connected" ? "ok" : "off"}`} />
          {backend === "connected" ? "control plane" : backend}
        </span>
        <span className={`pill ${auth?.profile || "STANDARD"}`}>{auth?.profile || "—"}</span>
        <span>{model}</span>
        <span>
          budget {auth?.budgets.tool_calls ?? 60} tools / {auth?.budgets.model_calls ?? 80} model
        </span>
        <span className="needle">Needle OFF</span>
        <span style={{ marginLeft: "auto" }}>
          RAD {status?.version || "1.0.1"}
          {isTauri() && (
            <button className="btn ghost" style={{ padding: "2px 8px", marginLeft: 10 }} onClick={() => void shutdown()}>
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
        Desktop is a surface over the existing Python API. It cannot run tools, raise budgets, or
        bypass Policy.decide.
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
  objectives: ObjectiveRow[];
  selectedId: string;
  setSelectedId: (id: string) => void;
  onAuth: (a: AuthoritySnapshot) => void;
  onRefresh: () => Promise<void>;
  go: (p: Page, id?: string) => void;
}) {
  switch (props.page) {
    case "chat":
      return <Chat client={props.client} go={props.go} />;
    case "objectives":
      return (
        <Objectives
          client={props.client}
          rows={props.objectives}
          selectedId={props.selectedId}
          onSelect={props.setSelectedId}
          onRefresh={props.onRefresh}
          go={props.go}
        />
      );
    case "execution":
      return <Execution client={props.client} id={props.selectedId} objectives={props.objectives} setId={props.setSelectedId} />;
    case "graph":
      return <Graph client={props.client} id={props.selectedId} objectives={props.objectives} setId={props.setSelectedId} />;
    case "trace":
      return <Trace client={props.client} id={props.selectedId} objectives={props.objectives} setId={props.setSelectedId} />;
    case "verification":
      return <Verification client={props.client} id={props.selectedId} objectives={props.objectives} setId={props.setSelectedId} />;
    case "artifacts":
      return <Artifacts client={props.client} id={props.selectedId} objectives={props.objectives} setId={props.setSelectedId} />;
    case "provenance":
      return <Provenance client={props.client} id={props.selectedId} objectives={props.objectives} setId={props.setSelectedId} />;
    case "usage":
      return <Usage client={props.client} go={props.go} />;
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

function Picker({
  id,
  setId,
  objectives,
}: {
  id: string;
  setId: (v: string) => void;
  objectives: ObjectiveRow[];
}) {
  return (
    <label>
      Objective
      <select value={id} onChange={(e) => setId(e.target.value)}>
        {!objectives.length && <option value="">None</option>}
        {objectives.map((o) => (
          <option key={o.id} value={o.id}>
            {o.goal.slice(0, 80)}
          </option>
        ))}
      </select>
    </label>
  );
}

function Chat({ client, go }: { client: RadClient; go: (p: Page, id?: string) => void }) {
  const [text, setText] = useState("");
  const [msgs, setMsgs] = useState<Array<{ who: "user" | "jerry"; text: string; proposal?: string }>>([]);
  const [busy, setBusy] = useState(false);
  const send = async (raw?: string) => {
    const t = (raw ?? text).trim();
    if (!t || busy) return;
    setText("");
    setMsgs((m) => [...m, { who: "user", text: t }]);
    setBusy(true);
    try {
      if (t === "run_tool" || t === "execute_tool" || t === "call_tool") {
        setMsgs((m) => [
          ...m,
          { who: "jerry", text: "Jerry has no tool runner. Tools run only through the executor / Policy.decide." },
        ]);
        return;
      }
      const r = await client.chat(t);
      const proposal = /^(build|create|write|research|implement|make|generate|plan|fix)\b/i.test(t) ? t : undefined;
      setMsgs((m) => [...m, { who: "jerry", text: r.reply, proposal }]);
    } catch (e) {
      setMsgs((m) => [...m, { who: "jerry", text: e instanceof Error ? e.message : String(e) }]);
    } finally {
      setBusy(false);
    }
  };
  const start = async (goal: string) => {
    setBusy(true);
    try {
      const o = await client.createObjective(goal, true);
      go("objectives", o.id);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="chat">
      <h1>Jerry</h1>
      <p className="lead">
        Operator layer over the RAD session. Tools still pass Policy.decide and the executor. Jerry
        cannot run a private tool path.
      </p>
      <div className="msgs">
        {msgs.length === 0 && (
          <div className="bubble jerry">
            Ask anything. Objectives you create go through the control plane.
            <div className="hint-col">
              {HINTS.map((h) => (
                <button key={h} className="btn ghost hint" onClick={() => void send(h)}>
                  {h}
                </button>
              ))}
            </div>
          </div>
        )}
        {msgs.map((m, i) => (
          <div key={i} className={`bubble ${m.who}`}>
            {m.text}
            {m.proposal && (
              <div className="proposal">
                <div className="muted">Proposed objective</div>
                <div>{m.proposal}</div>
                <button className="btn" disabled={busy} onClick={() => void start(m.proposal!)}>
                  Start on control plane
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
      <form
        className="row"
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          void send();
        }}
      >
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
        <button className="btn" disabled={busy} type="submit">
          Send
        </button>
      </form>
    </div>
  );
}

function Objectives({
  client,
  rows,
  selectedId,
  onSelect,
  onRefresh,
  go,
}: {
  client: RadClient;
  rows: ObjectiveRow[];
  selectedId: string;
  onSelect: (id: string) => void;
  onRefresh: () => Promise<void>;
  go: (p: Page, id?: string) => void;
}) {
  const [goal, setGoal] = useState("");
  const [detail, setDetail] = useState<ObjectiveRow & { tasks?: TaskRow[] } | null>(null);
  const [events, setEvents] = useState<EventRow[]>([]);
  const [err, setErr] = useState("");
  const loadDetail = useCallback(
    async (id: string) => {
      if (!id) {
        setDetail(null);
        return;
      }
      const [o, ev] = await Promise.all([client.objective(id), client.events(id)]);
      setDetail(o);
      setEvents(ev.events || []);
    },
    [client],
  );
  useEffect(() => {
    void loadDetail(selectedId);
    const t = window.setInterval(() => void loadDetail(selectedId), 1500);
    return () => window.clearInterval(t);
  }, [loadDetail, selectedId]);

  const create = async () => {
    setErr("");
    try {
      const o = await client.createObjective(goal);
      setGoal("");
      onSelect(o.id);
      await onRefresh();
      await loadDetail(o.id);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    }
  };
  const act = async (action: "pause" | "resume" | "cancel" | "run") => {
    if (!selectedId) return;
    setErr("");
    try {
      await client.lifecycle(selectedId, action);
      await onRefresh();
      await loadDetail(selectedId);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };
  return (
    <div>
      <h1>Objectives</h1>
      <p className="lead">
        Existing control plane. Desktop displays objectives, tasks and verification — it is not a React
        task engine.
      </p>
      <div className="card">
        <label>New objective</label>
        <input value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="goal" />
        <div className="row" style={{ marginTop: 10 }}>
          <button className="btn" onClick={() => void create()}>
            Create
          </button>
          <button className="btn ghost" onClick={() => void onRefresh()}>
            Refresh
          </button>
        </div>
        {err && <p className="err">{err}</p>}
      </div>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>id</th>
              <th>status</th>
              <th>verification</th>
              <th>goal</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((o) => (
              <tr
                key={o.id}
                onClick={() => onSelect(o.id)}
                style={{ cursor: "pointer", background: o.id === selectedId ? "var(--bg-3)" : undefined }}
              >
                <td>{o.id.slice(0, 12)}</td>
                <td>
                  <span className={`pill ${o.status}`}>{o.status}</span>
                </td>
                <td>
                  <Verify v={verifyLabel(o.verification)} />
                </td>
                <td>{o.goal}</td>
              </tr>
            ))}
            {!rows.length && (
              <tr>
                <td colSpan={4} className="muted">
                  No objectives yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {detail && (
        <div className="card">
          <div className="muted mono">{detail.id}</div>
          <h2 className="sub">{detail.goal}</h2>
          <div className="row">
            <span className={`pill ${detail.status}`}>{detail.status}</span>
            <Verify v={verifyLabel(detail.verification)} />
          </div>
          <div className="row" style={{ marginTop: 12 }}>
            <button className="btn" onClick={() => void act("run")}>
              Run
            </button>
            <button className="btn ghost" onClick={() => void act("pause")}>
              Pause
            </button>
            <button className="btn ghost" onClick={() => void act("resume")}>
              Resume
            </button>
            {detail.status === "needs_user" && (
              <button className="btn ghost" onClick={() => void act("resume")}>
                Recover
              </button>
            )}
            <button className="btn ghost" onClick={() => void act("cancel")}>
              Cancel
            </button>
            <button className="btn ghost" onClick={() => go("graph", detail.id)}>
              Graph
            </button>
          </div>
          {detail.result && <p className="lead">{detail.result}</p>}
          <TaskGraph tasks={detail.tasks || []} />
          <h3 className="sub">Live execution</h3>
          <EventLog events={events} tasks={detail.tasks || []} />
        </div>
      )}
    </div>
  );
}

function Verify({ v }: { v: string }) {
  if (!v || v === "—") return <span className="pill">not checked</span>;
  if (v === "VERIFIED") return <span className="pill COMPLETED">VERIFIED</span>;
  if (v === "FAILED") return <span className="pill FAILED">FAILED</span>;
  return <span className="pill VERIFYING">UNVERIFIED — not DONE</span>;
}

function TaskGraph({ tasks, current }: { tasks: TaskRow[]; current?: string }) {
  if (!tasks.length) return <p className="muted">No tasks yet. The planner has not produced a graph.</p>;
  return (
    <div className="graph">
      <p className="muted small">
        PENDING → READY → RUNNING → OBSERVING → VERIFYING → COMPLETED. FAILED → RETRYING → READY.
      </p>
      {tasks.map((t) => (
        <div key={t.id} className={`node ${t.id === current ? "current" : ""}`}>
          <div className="row">
            <span className={`pill ${t.status}`}>{t.status}</span>
            <Verify v={t.verification?.status || ""} />
            <span className="muted mono">{t.id}</span>
            {(t.attempts || 0) > 1 && <span className="warn">retry {t.attempts}</span>}
          </div>
          <div>{t.title || t.text || t.id}</div>
        </div>
      ))}
    </div>
  );
}

function EventLog({ events, tasks }: { events: EventRow[]; tasks: TaskRow[] }) {
  if (!events.length) return <p className="muted">No events yet.</p>;
  return (
    <ol className="elog">
      {events.slice(-80).map((e, i) => {
        const task = tasks.find((t) => t.id === e.task_id);
        return (
          <li key={`${e.seq}-${i}`}>
            <span className="muted">{new Date((e.at || 0) * (e.at < 1e12 ? 1000 : 1)).toLocaleTimeString()}</span>{" "}
            <span className="kind">{e.kind}</span>
            {task ? ` · ${task.title || task.text}` : ""}
          </li>
        );
      })}
    </ol>
  );
}

function useTrace(client: RadClient, id: string) {
  const [tasks, setTasks] = useState<TaskRow[]>([]);
  const [obs, setObs] = useState<ObservationRow[]>([]);
  const [arts, setArts] = useState<ArtifactRow[]>([]);
  const [obj, setObj] = useState<ObjectiveRow | null>(null);
  const [events, setEvents] = useState<EventRow[]>([]);
  useEffect(() => {
    if (!id) return;
    let stop = false;
    const load = async () => {
      try {
        const [t, ev] = await Promise.all([client.trace(id), client.events(id)]);
        if (stop) return;
        setObj(t.objective);
        setTasks(t.tasks || []);
        setObs(t.observations || []);
        setArts(t.artifacts || []);
        setEvents(ev.events || []);
      } catch {
        /* keep last */
      }
    };
    void load();
    const n = window.setInterval(() => void load(), 1500);
    return () => {
      stop = true;
      window.clearInterval(n);
    };
  }, [client, id]);
  return { tasks, obs, arts, obj, events };
}

function Execution({
  client,
  id,
  objectives,
  setId,
}: {
  client: RadClient;
  id: string;
  objectives: ObjectiveRow[];
  setId: (v: string) => void;
}) {
  const { tasks, events, obj } = useTrace(client, id);
  const running = tasks.find((t) => t.status === "RUNNING");
  return (
    <div>
      <h1>Live execution</h1>
      <p className="lead">Events from the control-plane log. This is not a second event system.</p>
      <div className="card">
        <Picker id={id} setId={setId} objectives={objectives} />
      </div>
      {running && (
        <div className="card">
          <div className="muted">current task</div>
          <div>{running.title || running.text}</div>
        </div>
      )}
      {obj && (
        <div className="row" style={{ marginBottom: 12 }}>
          <span className={`pill ${obj.status}`}>{obj.status}</span>
          <Verify v={verifyLabel(obj.verification)} />
        </div>
      )}
      <EventLog events={events} tasks={tasks} />
    </div>
  );
}

function Graph({
  client,
  id,
  objectives,
  setId,
}: {
  client: RadClient;
  id: string;
  objectives: ObjectiveRow[];
  setId: (v: string) => void;
}) {
  const { tasks, obj } = useTrace(client, id);
  return (
    <div>
      <h1>Task graph</h1>
      <p className="lead">Derived from persisted control-plane state.</p>
      <div className="card">
        <Picker id={id} setId={setId} objectives={objectives} />
      </div>
      <TaskGraph tasks={tasks} current={undefined} />
      {obj && <p className="muted">{obj.status}</p>}
    </div>
  );
}

function Trace({
  client,
  id,
  objectives,
  setId,
}: {
  client: RadClient;
  id: string;
  objectives: ObjectiveRow[];
  setId: (v: string) => void;
}) {
  const { obs } = useTrace(client, id);
  return (
    <div>
      <h1>Tool trace</h1>
      <p className="lead">Every tool call. Secrets are never shown. Desktop cannot run tools.</p>
      <div className="card">
        <Picker id={id} setId={setId} objectives={objectives} />
      </div>
      {obs.map((o) => (
        <article key={o.id} className="card">
          <div className="row">
            <span className="muted mono">{o.at ? new Date(o.at * (o.at < 1e12 ? 1000 : 1)).toLocaleTimeString() : ""}</span>
            <span className="pill">{o.tool}</span>
            <span className={`pill ${o.status === "success" ? "COMPLETED" : "FAILED"}`}>{o.status}</span>
          </div>
          <pre className="pre">{o.output}</pre>
        </article>
      ))}
      {!obs.length && <p className="muted">No tool calls yet.</p>}
    </div>
  );
}

function Verification({
  client,
  id,
  objectives,
  setId,
}: {
  client: RadClient;
  id: string;
  objectives: ObjectiveRow[];
  setId: (v: string) => void;
}) {
  const { tasks, obj } = useTrace(client, id);
  return (
    <div>
      <h1>Verification</h1>
      <p className="lead">Machine evidence only. A model's DONE claim is never shown as VERIFIED.</p>
      <div className="card">
        <Picker id={id} setId={setId} objectives={objectives} />
      </div>
      {obj && (
        <div className="card">
          <div className="row">
            <span>Objective</span>
            <Verify v={verifyLabel(obj.verification)} />
          </div>
        </div>
      )}
      {tasks.map((t) => (
        <article key={t.id} className="card">
          <div className="row">
            <span>{t.title || t.text}</span>
            <Verify v={t.verification?.status || ""} />
          </div>
          <ul className="muted">
            {(t.verification?.evidence || []).map((e, i) => (
              <li key={i}>
                {e.check} — {e.ok ? "pass" : "fail"} — {e.detail}
              </li>
            ))}
            {!t.verification?.evidence?.length && <li>no machine checks listed (UNVERIFIED, not VERIFIED)</li>}
          </ul>
        </article>
      ))}
    </div>
  );
}

function Artifacts({
  client,
  id,
  objectives,
  setId,
}: {
  client: RadClient;
  id: string;
  objectives: ObjectiveRow[];
  setId: (v: string) => void;
}) {
  const { arts } = useTrace(client, id);
  const [body, setBody] = useState("");
  const open = async (a: ArtifactRow) => {
    const r = await client.artifactBody(id, a.id);
    setBody(r.binary ? "(binary)" : r.text || "");
  };
  return (
    <div>
      <h1>Artifacts</h1>
      <p className="lead">Workspace files produced by tasks. No arbitrary browser filesystem access.</p>
      <div className="card">
        <Picker id={id} setId={setId} objectives={objectives} />
      </div>
      {arts.map((a) => (
        <button key={a.id} className="card art" onClick={() => void open(a)}>
          <div>{PathName(a.location)}</div>
          <div className="muted mono">
            {a.location} · sha256 {(a.sha256 || "").slice(0, 16)} · v{a.version}
          </div>
        </button>
      ))}
      {!arts.length && <p className="muted">No artifacts yet.</p>}
      {body && <pre className="pre">{body}</pre>}
    </div>
  );
}

function PathName(p: string) {
  const parts = p.replace(/\\/g, "/").split("/");
  return parts[parts.length - 1] || p;
}

function Provenance({
  client,
  id,
  objectives,
  setId,
}: {
  client: RadClient;
  id: string;
  objectives: ObjectiveRow[];
  setId: (v: string) => void;
}) {
  const [q, setQ] = useState("");
  const [report, setReport] = useState<Record<string, unknown> | null>(null);
  const go = async () => {
    if (!id || !q.trim()) return;
    setReport(await client.why(id, q.trim()));
  };
  return (
    <div>
      <h1>Provenance</h1>
      <p className="lead">creator → task → tool → observation → verification → artifact. Equivalent to rad why.</p>
      <div className="card">
        <Picker id={id} setId={setId} objectives={objectives} />
      </div>
      <div className="row">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="artifact path or claim" />
        <button className="btn" onClick={() => void go()}>
          Why
        </button>
      </div>
      {report && (
        <div className="chain">
          {Object.entries(report).map(([k, v]) => (
            <div key={k} className="card">
              <div className="muted">{k.toUpperCase()}</div>
              <pre className="pre">{typeof v === "string" ? v : JSON.stringify(v, null, 2)}</pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Usage({ client, go }: { client: RadClient; go: (p: Page, id?: string) => void }) {
  const [u, setU] = useState<Awaited<ReturnType<RadClient["usage"]>> | null>(null);
  useEffect(() => {
    void client.usage().then(setU);
    const t = window.setInterval(() => void client.usage().then(setU), 2500);
    return () => window.clearInterval(t);
  }, [client]);
  if (!u) return <p className="muted">Loading usage…</p>;
  return (
    <div>
      <h1>Usage</h1>
      <p className="lead">{u.note}</p>
      <div className="stats">
        {["tool_calls", "model_calls", "retries", "tokens", "paid_calls", "free_calls"].map((k) => (
          <div key={k} className="card">
            <div className="muted">{k.replace("_", " ")}</div>
            <div className="tabular">{u.totals[k] ?? 0}</div>
          </div>
        ))}
        <div className="card">
          <div className="muted">stored USD</div>
          <div className="tabular">{u.totals.money_usd ?? 0}</div>
        </div>
        <div className="card">
          <div className="muted">free-lock</div>
          <div>{u.free_lock ? "on" : "off"}</div>
        </div>
      </div>
      <p className="muted">{u.remaining_quota_note}</p>
      <table>
        <thead>
          <tr>
            <th>objective</th>
            <th>tools</th>
            <th>model</th>
            <th>tokens</th>
          </tr>
        </thead>
        <tbody>
          {u.per_objective.map((o) => (
            <tr key={o.id} onClick={() => go("objectives", o.id)} style={{ cursor: "pointer" }}>
              <td>{o.goal.slice(0, 48)}</td>
              <td>
                {o.usage.tool_calls}/{o.budget.tool_calls}
              </td>
              <td>
                {o.usage.model_calls}/{o.budget.model_calls}
              </td>
              <td>{o.usage.tokens}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const CONCEPT_CAPS = [
  "filesystem.read",
  "filesystem.write",
  "filesystem.delete",
  "shell.execute",
  "network.request",
  "browser.access",
  "mcp.use",
  "skills.install",
  "package.install",
  "process.spawn",
  "model.free",
  "model.paid",
];

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
  const [custom, setCustom] = useState<Record<string, string>>({});
  const [workspaceOnly, setWorkspaceOnly] = useState(auth.scopes.workspace_only);
  const [extraPaths, setExtraPaths] = useState(auth.scopes.extra_paths.join("\n"));
  const [hosts, setHosts] = useState(auth.scopes.hosts.join("\n"));
  const [customConfirm, setCustomConfirm] = useState<"ask" | "never">("ask");
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");
  useEffect(() => {
    setProfile(auth.profile);
    const caps: Record<string, string> = {};
    for (const [k, v] of Object.entries(auth.capabilities)) caps[k] = v.effect;
    setCustom(caps);
    setWorkspaceOnly(auth.scopes.workspace_only);
    setExtraPaths(auth.scopes.extra_paths.join("\n"));
    setHosts(auth.scopes.hosts.join("\n"));
  }, [auth]);
  const apply = async () => {
    setErr("");
    setOk("");
    try {
      const next = await client.setAuthority({
        profile,
        confirm_unrestricted: profile === "UNRESTRICTED" ? confirmU : undefined,
        capabilities: profile === "CUSTOM" ? custom : undefined,
        confirmation: profile === "CUSTOM" ? customConfirm : undefined,
        scopes: {
          workspace_only: workspaceOnly,
          extra_paths: extraPaths.split("\n").map((s) => s.trim()).filter(Boolean),
          hosts: hosts.split("\n").map((s) => s.trim()).filter(Boolean),
        },
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
        Authority is what is allowed. Scope is how far. Confirmation is whether to ask. Budget and
        Policy.decide stay in the Python core. Automatic confirmation only changes ASK→ALLOW.
      </p>
      {auth.unrestricted && (
        <div className="banner">
          UNRESTRICTED is explicitly user-authorized autonomy — not a hidden or “unsafe by definition”
          path. Hard layer, executor, budgets, audit, provenance and verification remain. It does not
          remove provider/model content policies.
        </div>
      )}
      <div className="card">
        <label>Authority profile</label>
        <select value={profile} onChange={(e) => setProfile(e.target.value as Profile)}>
          {["SAFE", "STANDARD", "AUTONOMOUS", "UNRESTRICTED", "CUSTOM"].map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <p className="lead" style={{ marginTop: 10 }}>
          {auth.blurb}
        </p>
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
        {profile === "CUSTOM" && (
          <div className="grid" style={{ marginTop: 12 }}>
            {CONCEPT_CAPS.map((cap) => (
              <label key={cap}>
                {cap}
                <select value={custom[cap] || "ASK"} onChange={(e) => setCustom((c) => ({ ...c, [cap]: e.target.value }))}>
                  {["ALLOW", "ASK", "LIMITED", "DENY"].map((eff) => (
                    <option key={eff} value={eff}>
                      {eff}
                    </option>
                  ))}
                </select>
              </label>
            ))}
            <label>
              Confirmation
              <select value={customConfirm} onChange={(e) => setCustomConfirm(e.target.value as "ask" | "never")}>
                <option value="ask">always required (ask)</option>
                <option value="never">automatic (ASK→ALLOW only)</option>
              </select>
            </label>
          </div>
        )}
        {(profile === "CUSTOM" || profile === "UNRESTRICTED" || profile === "AUTONOMOUS") && (
          <div style={{ marginTop: 12 }}>
            <label>
              <input
                type="checkbox"
                checked={workspaceOnly}
                onChange={(e) => setWorkspaceOnly(e.target.checked)}
                style={{ width: "auto", marginRight: 8 }}
              />
              workspace-only
            </label>
            <label>
              Extra paths (server-validated, no `..`)
              <textarea value={extraPaths} onChange={(e) => setExtraPaths(e.target.value)} />
            </label>
            <label>
              Hosts
              <textarea value={hosts} onChange={(e) => setHosts(e.target.value)} />
            </label>
          </div>
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
        <div>
          {auth.confirmation}{" "}
          {auth.confirmation_is_automatic
            ? "(ASK→ALLOW; DENY/hard/budget/scope/verification unchanged)"
            : "(always required for ASK)"}
        </div>
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
        <div>Auto via HTTP: {String(status?.auto)} — comes from authority confirmation, not a UI toggle</div>
      </div>
    </div>
  );
}

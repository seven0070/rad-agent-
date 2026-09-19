/** Jerry — operator loop. Conversation through POST /v1/chat (Session brain);
 *  every status card below is fetched from the backend. Jerry never fabricates
 *  completion or verification: the cards only render what /v1 returned. */
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, Artifact, ObjectiveRow, RecoveryView, WhyArtifact } from "../api";
import { useRad } from "../ctx";
import { fmtAgo, fmtTime, redactText } from "../util";

interface Msg {
  who: "user" | "jerry";
  text: string;
  at: number;
}

export default function Jerry() {
  const { client, selected, select, selectedId, refresh } = useRad();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [goal, setGoal] = useState("");
  const [goalErr, setGoalErr] = useState("");
  const [creating, setCreating] = useState(false);
  const [focus, setFocus] = useState<ObjectiveRow | null>(null);
  const boxRef = useRef<HTMLDivElement>(null);

  // follow the selected objective, else the newest one
  useEffect(() => {
    if (selected) {
      setFocus(selected);
      return;
    }
    void client.objectives(false).then((r) => {
      const last = r.objectives[0] || null;
      setFocus(last);
    });
  }, [selected, client, selectedId]);

  useEffect(() => {
    boxRef.current?.scrollTo(0, boxRef.current.scrollHeight);
  }, [msgs]);

  const send = async () => {
    const t = text.trim();
    if (!t || busy) return;
    setText("");
    setMsgs((m) => [...m, { who: "user", text: t, at: Date.now() / 1000 }]);
    setBusy(true);
    try {
      const r = await client.chat(t);
      setMsgs((m) => [...m, { who: "jerry", text: redactText(r.reply || "(empty reply)"), at: Date.now() / 1000 }]);
    } catch (e) {
      setMsgs((m) => [
        ...m,
        { who: "jerry", text: e instanceof ApiError ? `backend error (${e.status}): ${e.message}` : String(e), at: Date.now() / 1000 },
      ]);
    } finally {
      setBusy(false);
      void refresh();
    }
  };

  const createObjective = async () => {
    const g = goal.trim();
    if (!g || creating) return;
    setCreating(true);
    setGoalErr("");
    try {
      const o = await client.createObjective(g, true);
      setGoal("");
      select(o.id);
      setMsgs((m) => [
        ...m,
        {
          who: "jerry",
          text: o.started
            ? `Objective ${o.id} created and started. Authority at creation: see the Authority tab. I will report real status only.`
            : `Objective ${o.id} created PENDING (the backend is not in auto-confirmation mode). Use Run when you are ready.`,
          at: Date.now() / 1000,
        },
      ]);
      await refresh();
    } catch (e) {
      setGoalErr(e instanceof ApiError ? e.message : String(e));
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="jerry">
      <div className="jerry-chat">
        <h1>Jerry</h1>
        <p className="lead">
          Operator over the RAD session. Tools still pass Policy.decide and the executor —
          Jerry cannot run a private tool path.
        </p>
        <div className="msgs" ref={boxRef}>
          {msgs.length === 0 && (
            <div className="bubble jerry">
              Tell me the objective. Example: “Build a FastAPI service with tests.” I will show
              the authority that applies before anything runs, and I only report status the
              backend actually recorded.
            </div>
          )}
          {msgs.map((m, i) => (
            <div key={i} className={`bubble ${m.who}`}>
              <span className="bubble-meta">{m.who} · {fmtAgo(m.at)}</span>
              {m.text}
            </div>
          ))}
          {busy && <div className="bubble jerry"><span className="bubble-meta">jerry</span>thinking…</div>}
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
      <div className="jerry-side">
        <ObjectiveCard
          focus={focus}
          onFollow={(id) => select(id)}
          onFollowNone={() => select(null)}
        />
        <div className="card">
          <label>New objective</label>
          <textarea
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="e.g. Build a FastAPI service with tests"
            style={{ minHeight: 64 }}
          />
          <div className="row" style={{ marginTop: 10 }}>
            <button className="btn" disabled={creating || !goal.trim()} onClick={() => void createObjective()}>
              {creating ? "Creating…" : "Create Objective"}
            </button>
            <span className="hint">
              created through the control plane; runs only when the backend allows
            </span>
          </div>
          {goalErr && <p className="err">{goalErr}</p>}
        </div>
      </div>
    </div>
  );
}

function ObjectiveCard({
  focus,
  onFollow,
  onFollowNone,
}: {
  focus: ObjectiveRow | null;
  onFollow: (id: string) => void;
  onFollowNone: () => void;
}) {
  const { client } = useRad();
  const [recovery, setRecovery] = useState<RecoveryView | null>(null);
  const [planSummary, setPlanSummary] = useState("");
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [why, setWhy] = useState<WhyArtifact | null>(null);
  const [whyErr, setWhyErr] = useState("");
  const [lastUsed, setLastUsed] = useState<string>("");
  const [acting, setActing] = useState(false);

  const oid = focus?.id;
  const status = (focus?.status || "").toLowerCase();

  const loadContext = useCallback(async () => {
    if (!oid) {
      setRecovery(null);
      setPlanSummary("");
      setArtifacts([]);
      setWhy(null);
      return;
    }
    const [rec, plan, arts] = await Promise.all([
      client.recovery(oid).catch(() => null),
      client.plan(oid).catch(() => null),
      client.artifacts(oid).catch(() => null),
    ]);
    setRecovery(rec);
    if (plan) {
      const done = plan.tasks.filter((t) => t.status === "COMPLETED").length;
      setPlanSummary(
        `plan v${plan.plan_version} (${plan.source || "unknown source"}): ${plan.tasks.length} tasks, ${done} completed` +
          (plan.replans.length ? `, ${plan.replans.length} replan(s)` : ""),
      );
    } else {
      setPlanSummary("no plan yet");
    }
    setArtifacts(arts ? arts.artifacts.slice(0, 5) : []);
  }, [client, oid]);

  useEffect(() => {
    setLastUsed("");
    void loadContext();
  }, [loadContext, status]);

  const act = async (action: "pause" | "resume" | "cancel" | "run") => {
    if (!oid || acting) return;
    setActing(true);
    setLastUsed("");
    try {
      const r = await client.objectiveAction(oid, action);
      setLastUsed(`${action} accepted → ${r.status}`);
      await loadContext();
    } catch (e) {
      setLastUsed(e instanceof ApiError ? `${action} refused: ${e.message}` : String(e));
    } finally {
      setActing(false);
    }
  };

  const explainProvenance = async (ref: string) => {
    if (!oid) return;
    setWhyErr("");
    setWhy(null);
    try {
      const w = await client.why(oid, ref);
      setWhy(w as WhyArtifact);
    } catch (e) {
      setWhyErr(e instanceof ApiError ? e.message : String(e));
    }
  };

  if (!focus) {
    return (
      <div className="card">
        <label>Current objective</label>
        <div className="hint">none yet — create one on the right</div>
        <div className="row" style={{ marginTop: 8 }}>
          <button className="btn ghost" onClick={onFollowNone}>
            All objectives
          </button>
        </div>
      </div>
    );
  }

  const needsUser = status === "needs_user";
  const canPause = status === "running" || status === "planning";
  const canResume = ["paused", "needs_user", "failed", "pending"].includes(status);
  const canRun = status === "pending";
  const ver = (focus.verification || "").toUpperCase();

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <div>
          <span className={`pill ${objStatusPill(status)}`}>{focus.status}</span>{" "}
          <b>{focus.id}</b>
        </div>
        <button className="btn ghost" style={{ padding: "3px 10px" }} onClick={() => onFollow(focus.id)}>
          Follow →
        </button>
      </div>
      <div style={{ marginTop: 8, whiteSpace: "pre-wrap", fontSize: 13 }}>{focus.goal}</div>
      <div className="hint" style={{ marginTop: 6 }}>
        updated {fmtAgo(focus.updated)} · {focus.result_summary || focus.failure || "no result recorded yet"}
      </div>

      {ver && (
        <div className={`ver-line ${ver === "VERIFIED" ? "ok" : ver === "FAILED" ? "err" : "hint"}`} style={{ marginTop: 8 }}>
          verification: {ver || "none"} — model “DONE” is never counted as verified
        </div>
      )}

      {planSummary && <div className="hint" style={{ marginTop: 6 }}>{planSummary}</div>}

      {focus.usage && (
        <div className="hint" style={{ marginTop: 4 }}>
          tools {focus.usage.tool_calls ?? 0} / budget {focus.budget?.tool_calls || "∞"} · model{" "}
          {focus.usage.model_calls ?? 0} / {focus.budget?.model_calls || "∞"} · retries{" "}
          {focus.usage.retries ?? 0} / {focus.budget?.retries || "∞"} · ${focus.usage.money_usd ?? 0}
        </div>
      )}

      {needsUser && (
        <div className="banner" style={{ marginTop: 10 }}>
          <b>NEEDS_USER</b> — intervention required.
          <div style={{ marginTop: 4 }}>{redactText(focus.failure || focus.result_summary || "the backend recorded a NEEDS_USER state")}</div>
          <div className="row" style={{ marginTop: 8 }}>
            <button className="btn" disabled={acting} onClick={() => void act("resume")}>
              Resolve (resume)
            </button>
            <button className="btn ghost" disabled={acting} onClick={() => void act("cancel")}>
              Cancel objective
            </button>
          </div>
        </div>
      )}

      {recovery && recovery.decisions.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <label>Recovery (backend decisions)</label>
          {recovery.decisions.slice(-3).map((d, i) => (
            <div key={i} className="hint" style={{ marginBottom: 4 }}>
              {fmtTime(d.at)} · {d.failure_class} → {d.strategy}: {redactText(d.reason)}
            </div>
          ))}
        </div>
      )}

      {artifacts.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <label>Artifacts (latest)</label>
          {artifacts.map((a) => (
            <div key={a.id} className="row" style={{ marginBottom: 4 }}>
              <span className="hint" style={{ flex: 1 }}>
                {a.location} (v{a.version})
              </span>
              <button className="btn ghost" style={{ padding: "2px 8px" }} onClick={() => void explainProvenance(a.location)}>
                why?
              </button>
            </div>
          ))}
          {whyErr && <p className="err">{whyErr}</p>}
          {why && (
            <div className="why" style={{ marginTop: 8 }}>
              <div className="hint">
                {why.task.text || why.task.id} → action {why.action ? `${why.action.tool}` : "—"} →{" "}
                {why.versions.length} version(s) · evidence {why.evidence.length}
              </div>
              {why.evidence.slice(0, 4).map((e, i) => (
                <div key={i} className="hint" style={{ marginTop: 4 }}>
                  {String((e as { source?: string }).source || (e as { kind?: string }).kind || "evidence")}{" "}
                  {String((e as { excerpt?: string }).excerpt || "").slice(0, 160)}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="row" style={{ marginTop: 12 }}>
        {canRun && (
          <button className="btn" disabled={acting} onClick={() => void act("run")}>
            Run (plan + start)
          </button>
        )}
        {canResume && !canRun && (
          <button className="btn" disabled={acting} onClick={() => void act("resume")}>
            Resume
          </button>
        )}
        {canPause && (
          <button className="btn ghost" disabled={acting} onClick={() => void act("pause")}>
            Pause
          </button>
        )}
        {!["completed", "cancelled", "expired"].includes(status) && (
          <button className="btn ghost" disabled={acting} onClick={() => void act("cancel")}>
            Cancel
          </button>
        )}
      </div>
      {lastUsed && <p className="hint" style={{ marginTop: 6 }}>{lastUsed}</p>}
    </div>
  );
}

function objStatusPill(s: string): string {
  const k = s.toLowerCase();
  if (k === "completed") return "STANDARD";
  if (k === "failed") return "UNRESTRICTED";
  if (k === "needs_user") return "AUTONOMOUS";
  return "STANDARD";
}

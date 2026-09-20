/** Live execution view. Polls GET /v1/objectives/{id}/live (backend state only).
 *  No client-side scheduling; pause/resume/cancel are backend operations. */
import { useEffect, useRef, useState } from "react";
import { ApiError, LiveView } from "../api";
import { useRad } from "../ctx";
import { budgetPct, fmtElapsed, objStatusClass, redactText, taskStateClass } from "../util";

export default function ActiveRun() {
  const { client, selected } = useRad();
  const [live, setLive] = useState<LiveView | null>(null);
  const [err, setErr] = useState("");
  const [now, setNow] = useState(Date.now() / 1000);
  const [acting, setActing] = useState("");
  const sinceRef = useRef(0);
  const id = selected?.id;

  useEffect(() => {
    sinceRef.current = 0;
    setLive(null);
    setErr("");
    if (!id) return;
    let stop = false;
    const tick = async () => {
      try {
        const l = await client.live(id, sinceRef.current, 50);
        if (stop) return;
        if (l.events.length) sinceRef.current = l.events[l.events.length - 1].seq;
        setLive(l);
        setErr("");
      } catch (e) {
        if (!stop) setErr(e instanceof ApiError ? e.message : String(e));
      }
    };
    void tick();
    const t = setInterval(tick, 2000);
    const clock = setInterval(() => setNow(Date.now() / 1000), 1000);
    return () => {
      stop = true;
      clearInterval(t);
      clearInterval(clock);
    };
  }, [client, id]);

  if (!id) {
    return (
      <div>
        <h1>Active Run</h1>
        <p className="lead">No objective selected. Pick one in Objectives, or create one.</p>
      </div>
    );
  }

  const act = async (a: "pause" | "resume" | "cancel") => {
    setActing(a);
    try {
      await client.objectiveAction(id, a);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    } finally {
      setActing("");
    }
  };

  const l = live;
  const status = (l?.status || "").toLowerCase();
  const usage = l?.usage || {};
  const budget = l?.budget || {};
  const toolUsed = Number(usage.tool_calls ?? 0);
  const toolBudget = Number(budget["tool_calls"] ?? 0);
  const modelUsed = Number(usage.model_calls ?? 0);
  const modelBudget = Number(budget["model_calls"] ?? 0);
  const tokens = Number(usage.tokens ?? 0);
  const tokenBudget = Number(budget["tokens"] ?? 0);
  const money = Number(usage.money_usd ?? 0);
  const moneyBudget = Number(budget["money_usd"] ?? 0);

  const taskElapsed = l?.current_task?.started ? now - (l.current_task.started as number) : 0;
  const objElapsed = l ? now - (l.objective.created || now) : 0;

  // provider from the most recent MODEL_CALLED/MODEL_SELECTED event
  let provider = "";
  for (const e of [...(l?.events || [])].reverse()) {
    const p = e.data.provider;
    if ((e.kind === "MODEL_CALLED" || e.kind === "MODEL_SELECTED") && p) {
      provider = String(p);
      break;
    }
  }

  const lastRecovery = (l?.events || []).filter((e) => e.kind === "RECOVERY_DECISION").slice(-1)[0];
  const done = l?.tasks.by_status["COMPLETED"] ?? 0;
  const total = l?.tasks.total ?? 0;

  return (
    <div>
      <h1>Active Run</h1>
      <p className="lead">
        <span className={`badge ${objStatusClass(l?.status || "pending")}`}>{l?.status || "…"}</span>{" "}
        {l?.objective.id} · <span className="hint">{l?.objective.goal}</span>
      </p>
      {err && <p className="err">{err}</p>}
      {!l && !err && <p className="lead">loading…</p>}

      {l && (
        <>
          <div className="row" style={{ marginBottom: 14 }}>
            {["running", "planning"].includes(status) && (
              <button className="btn" disabled={!!acting} onClick={() => void act("pause")}>
                {acting === "pause" ? "Pausing…" : "Pause"}
              </button>
            )}
            {["paused", "needs_user", "failed"].includes(status) && (
              <button className="btn" disabled={!!acting} onClick={() => void act("resume")}>
                {acting === "resume" ? "Resuming…" : "Resume"}
              </button>
            )}
            {["pending", "planning", "running", "paused", "needs_user"].includes(status) && (
              <button className="btn warn" disabled={!!acting} onClick={() => void act("cancel")}>
                {acting === "cancel" ? "Cancelling…" : "Cancel"}
              </button>
            )}
          </div>

          <div className="grid">
            <div className="card stat">
              <label>Current task</label>
              {l.current_task ? (
                <>
                  <b className={`badge ${taskStateClass(l.current_task.status)}`}>{l.current_task.status}</b>
                  <div style={{ marginTop: 6, fontSize: 13, whiteSpace: "pre-wrap" }}>{redactText(l.current_task.text)}</div>
                  <div className="hint" style={{ marginTop: 4 }}>
                    attempt {l.current_task.attempts} · elapsed {fmtElapsed(taskElapsed)}
                  </div>
                </>
              ) : (
                <div className="hint">none in flight</div>
              )}
            </div>
            <div className="card stat">
              <label>Task progress</label>
              <div style={{ fontSize: 22, fontWeight: 650 }}>
                {done}/{total}
              </div>
              <div className="meter">
                <div className="meter-fill" style={{ width: `${total ? (done / total) * 100 : 0}%` }} />
              </div>
              <div className="hint" style={{ marginTop: 6 }}>
                {Object.entries(l.tasks.by_status)
                  .filter(([, n]) => n)
                  .map(([s, n]) => (
                    <span key={s} className={`badge ${taskStateClass(s)}`} style={{ marginRight: 4 }}>
                      {s} {n}
                    </span>
                  ))}
              </div>
            </div>
            <div className="card stat">
              <label>Budget (backend-enforced)</label>
              <BudgetBar label="tools" used={toolUsed} total={toolBudget} />
              <BudgetBar label="model" used={modelUsed} total={modelBudget} />
              <BudgetBar label="retries" used={Number(l.retries.used)} total={Number(l.retries.budget)} />
              <BudgetBar label="tokens" used={tokens} total={tokenBudget} />
              <BudgetBar label="money" used={money} total={moneyBudget} money />
            </div>
            <div className="card stat">
              <label>Execution</label>
              <div className="kv"><span>objective elapsed</span><b>{fmtElapsed(objElapsed)}</b></div>
              <div className="kv"><span>provider</span><b>{provider || "—"}</b></div>
              <div className="kv"><span>tokens (in+out)</span><b>{tokens}</b></div>
              <div className="kv"><span>artifacts</span><b>{l.artifacts}</b></div>
              <div className="kv"><span>verification</span><b>{l.verification || "in progress"}</b></div>
              {lastRecovery && (
                <div className="hint" style={{ marginTop: 6 }}>
                  ↻ {String(lastRecovery.data.failure_class)} → {String(lastRecovery.data.strategy)}
                </div>
              )}
            </div>
          </div>

          <div className="card">
            <label>Event feed (newest last; secrets redacted)</label>
            <div className="feed">
              {(l.events || []).slice(-40).map((e) => (
                <div key={e.seq} className="feed-row">
                  <span className="hint">{new Date(e.at * 1000).toLocaleTimeString()}</span>
                  <span className="feed-kind">{e.kind}</span>
                  {e.task_id && <span className="hint">{e.task_id}</span>}
                  <span className="feed-data">{feedSummary(e.data)}</span>
                </div>
              ))}
              {(l.events || []).length === 0 && <div className="hint">no new events</div>}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function BudgetBar({ label, used, total, money }: { label: string; used: number; total: number; money?: boolean }) {
  const pct = budgetPct(used, total);
  const fmt = (v: number) => (money ? `$${v.toFixed(3)}` : String(Math.round(v)));
  return (
    <div style={{ marginBottom: 8 }}>
      <div className="row" style={{ gap: 6 }}>
        <span className="hint" style={{ width: 64 }}>{label}</span>
        <div className="meter" style={{ flex: 1 }}>
          <div className={`meter-fill ${pct >= 90 ? "hot" : ""}`} style={{ width: `${pct}%` }} />
        </div>
        <span className="hint" style={{ width: 92, textAlign: "right" }}>
          {fmt(used)} / {total ? fmt(total) : "∞"}
        </span>
      </div>
    </div>
  );
}

function feedSummary(d: Record<string, unknown>): string {
  const bits: string[] = [];
  for (const k of ["tool", "status", "strategy", "failure_class", "reason", "summary", "note", "text", "provider", "tokens"]) {
    const v = d[k];
    if (v !== undefined && v !== null && v !== "") bits.push(`${k}=${String(v).slice(0, 90)}`);
  }
  return redactText(bits.join(" · ").slice(0, 220));
}

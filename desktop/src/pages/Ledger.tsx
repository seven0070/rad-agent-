// Ledger.tsx — the replication trail in the cockpit.
// Data: sidecar GET /api/ledger (wraps rad.desktop_ledger.folded/summary).
// Verdict chips: CONFIRMED=green, NOT_REPLICATED=red, INCONCLUSIVE=amber.
// Amendments render inline under their battle (provenance visible, never hidden).

import { useEffect, useState } from "react";
import { useRad } from "../ctx";

type Amendment = { field: string; was: string; now: string; reason: string; amended_at: string };
type Battle = {
  battle_id: string; slug: string; paper_title?: string;
  replication_verdict: string; battle_verdict?: string; seed?: number;
  task_count?: number; ledger_ts?: string; pareto_tradeoff?: boolean;
  claimed?: { claim: string; claimed_gain: string }[];
  measured?: Record<string, { baseline: number; candidate: number; delta: number; n: number }>;
  amendments?: Amendment[];
  _amendments?: Amendment[];
};
type LedgerData = {
  format: string; version: number; battles: Battle[]; amendment_count: number;
  summary?: { battles: number; replication_rate: number; verdicts: Record<string, number> };
};

const VERDICT_STYLE: Record<string, string> = {
  CONFIRMED: "chip-green", NOT_REPLICATED: "chip-red",
  INCONCLUSIVE: "chip-amber", NO_CLAIM_TO_TEST: "chip-gray",
};

export default function Ledger() {
  const { client } = useRad();
  const [data, setData] = useState<LedgerData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        let d: LedgerData;
        if (client) {
          d = await client.ledger();
        } else {
          const res = await fetch("/api/ledger");
          if (!res.ok) throw new Error(`sidecar ${res.status}`);
          d = (await res.json()) as LedgerData;
        }
        if (alive) { setData(d); setErr(null); }
      } catch (e) {
        if (alive) setErr(String(e));
      }
    };
    void load();
    const t = setInterval(load, 15_000);                 // light polling, Memory.tsx cadence
    return () => { alive = false; clearInterval(t); };
  }, [client]);

  if (err) return <div className="page"><h2>Ledger</h2><p className="muted">sidecar unreachable: {err}</p></div>;
  if (!data) return <div className="page"><h2>Ledger</h2><p className="muted">reading _ledger.jsonl…</p></div>;

  const s = data.summary;
  return (
    <div className="page">
      <h2>Replication Ledger</h2>
      <div className="ledger-head">
        <span className="stat">{s?.battles ?? data.battles.length} battles</span>
        <span className="stat">replication rate <b>{s ? Math.round((s.replication_rate ?? 0) * 100) : 0}%</b></span>
        <span className="stat">{data.amendment_count} amendments</span>
        <span className="stat muted">append-only · amendments fold, history never erased</span>
      </div>

      {data.battles.length === 0 && (
        <p className="muted">No battles yet — <code>rad paper add &lt;arxiv-id&gt;</code> begins the trail.</p>
      )}

      {data.battles.map((bt) => (
        <div key={bt.battle_id} className="battle-card">
          <div className="battle-row">
            <span className={`chip ${VERDICT_STYLE[bt.replication_verdict] ?? "chip-gray"}`}>
              {bt.replication_verdict}
            </span>
            <span className="battle-title">{bt.paper_title || bt.slug}</span>
            {bt.pareto_tradeoff && (
              <span className="chip chip-amber" title="claim won; an observational metric regressed">
                pareto tradeoff
              </span>
            )}
          </div>
          <div className="battle-meta muted">
            {bt.battle_id} · seed {bt.seed ?? "—"} · {bt.task_count ?? "—"} tasks
            {bt.ledger_ts ? ` · ${bt.ledger_ts.slice(0, 16).replace("T", " ")}` : ""}
          </div>
          {bt.measured && (
            <div className="metrics-row">
              {Object.entries(bt.measured).map(([m, d]) => (
                <span key={m} className="metric" title={`baseline ${d.baseline} → candidate ${d.candidate} (n=${d.n})`}>
                  {m}: {d.delta > 0 ? "+" : ""}{d.delta}
                </span>
              ))}
            </div>
          )}
          {(bt.amendments ?? bt._amendments ?? []).map((a, i) => (
            <div key={i} className="amendment">
              ⚖ amended: <b>{a.was}</b> → <b>{a.now}</b> — {a.reason}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

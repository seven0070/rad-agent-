// Ledger.tsx — the replication trail in the cockpit.
// Data: sidecar GET /api/ledger (wraps rad.desktop_ledger.folded/summary).
// Verdict chips: CONFIRMED=green, NOT_REPLICATED=red, INCONCLUSIVE=amber.
// Amendments render inline under their battle (provenance visible, never hidden).

import { useCallback, useEffect, useState } from "react";
import { RadClient } from "../api";
import { useRad } from "../ctx";
import {
  IconLedger,
  IconAmendment,
  IconRefresh,
} from "../components/Icons";
import { Skeleton } from "../components/Skeleton";

type Amendment = {
  field: string;
  was: string;
  now: string;
  reason: string;
  amended_at: string;
};

type Battle = {
  battle_id: string;
  slug: string;
  paper_title?: string;
  replication_verdict: string;
  battle_verdict?: string;
  seed?: number;
  task_count?: number;
  ledger_ts?: string;
  pareto_tradeoff?: boolean;
  claimed?: { claim: string; claimed_gain: string }[];
  measured?: Record<
    string,
    { baseline: number; candidate: number; delta: number; n: number }
  >;
  amendments?: Amendment[];
  _amendments?: Amendment[];
};

type LedgerData = {
  format: string;
  version: number;
  battles: Battle[];
  amendment_count: number;
  summary?: {
    battles: number;
    replication_rate: number;
    verdicts: Record<string, number>;
  };
};

const VERDICT_STYLE: Record<string, { chip: string; dot: string }> = {
  CONFIRMED: { chip: "chip-green", dot: "var(--emerald-verif)" },
  NOT_REPLICATED: { chip: "chip-red", dot: "var(--rose-danger)" },
  INCONCLUSIVE: { chip: "chip-amber", dot: "var(--rad-amber)" },
  NO_CLAIM_TO_TEST: { chip: "chip-gray", dot: "var(--text-muted)" },
};

export default function Ledger() {
  const { client } = useRad();
  const [data, setData] = useState<LedgerData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(
    async (showRefreshing = false) => {
      if (showRefreshing) setRefreshing(true);
      try {
        const c = client || new RadClient("", "");
        const d: LedgerData = await c.ledger();
        setData(d);
        setErr(null);
      } catch (e) {
        setErr(String(e));
      } finally {
        setLoading(false);
        if (showRefreshing) setRefreshing(false);
      }
    },
    [client],
  );

  useEffect(() => {
    let alive = true;
    const fetchLedger = async () => {
      if (alive) await load();
    };
    void fetchLedger();
    const t = setInterval(fetchLedger, 15_000); // light polling, Memory.tsx cadence
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, [load]);

  if (err && !data) {
    return (
      <div className="page" role="region" aria-label="Replication Ledger">
        <div className="page-header">
          <div className="page-title-group">
            <h2>
              <IconLedger size={20} style={{ color: "var(--rad-indigo)" }} />
              Replication Ledger
            </h2>
            <p className="lead">Sidecar unreachable</p>
          </div>
          <button className="btn ghost" onClick={() => void load(true)}>
            <IconRefresh size={13} style={{ marginRight: 6 }} />
            Retry
          </button>
        </div>
        <div className="card" style={{ borderColor: "rgba(244, 63, 94, 0.3)" }}>
          <p className="err">{err}</p>
        </div>
      </div>
    );
  }

  if (loading && !data) {
    return <LedgerSkeleton />;
  }

  if (!data) return null;

  const s = data.summary;
  const repRate = s ? Math.round((s.replication_rate ?? 0) * 100) : 0;

  return (
    <div className="page" role="region" aria-label="Replication Ledger">
      {/* Page Header */}
      <div className="page-header">
        <div className="page-title-group">
          <h2>
            <IconLedger size={20} style={{ color: "var(--rad-indigo)" }} />
            Replication Ledger
          </h2>
          <p className="lead">
            Empirical replication trail. Append-only ledger; amendments fold with
            strict provenance, raw history never erased.
          </p>
        </div>
        <button
          className="btn ghost mini"
          onClick={() => void load(true)}
          disabled={refreshing}
          aria-label="Refresh ledger"
        >
          <IconRefresh
            size={12}
            className={refreshing ? "spin" : ""}
            style={{ marginRight: 5 }}
          />
          {refreshing ? "Polling…" : "Refresh"}
        </button>
      </div>

      {/* Summary Stat Bar */}
      <div className="ledger-head" role="status">
        <span className="stat">
          <b>{s?.battles ?? data.battles.length}</b> battles
        </span>
        <span className="stat">
          replication rate{" "}
          <b
            style={{
              color:
                repRate >= 80
                  ? "var(--emerald-verif)"
                  : repRate >= 50
                    ? "var(--rad-amber)"
                    : "var(--rose-danger)",
            }}
          >
            {repRate}%
          </b>
        </span>
        <span className="stat">
          <b>{data.amendment_count}</b> amendments
        </span>
        <span className="stat muted" style={{ marginLeft: "auto", fontSize: 11 }}>
          append-only · amendments fold, history preserved
        </span>
      </div>

      {/* Empty State */}
      {data.battles.length === 0 && (
        <div className="card" style={{ textAlign: "center", padding: "32px 20px" }}>
          <p className="muted" style={{ margin: 0 }}>
            No battles recorded yet — <code>rad paper add &lt;arxiv-id&gt;</code> begins the trail.
          </p>
        </div>
      )}

      {/* Battle Cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {data.battles.map((bt) => {
          const style =
            VERDICT_STYLE[bt.replication_verdict] ?? VERDICT_STYLE.NO_CLAIM_TO_TEST;
          const amendments = bt.amendments ?? bt._amendments ?? [];

          return (
            <article
              key={bt.battle_id}
              className="battle-card"
              aria-labelledby={`battle-${bt.battle_id}-title`}
            >
              <div className="battle-row">
                <span className={`chip ${style.chip}`}>
                  <span
                    className="dot"
                    style={{ backgroundColor: style.dot, width: 6, height: 6 }}
                  />
                  {bt.replication_verdict}
                </span>
                <span
                  className="battle-title"
                  id={`battle-${bt.battle_id}-title`}
                >
                  {bt.paper_title || bt.slug}
                </span>
                {bt.pareto_tradeoff && (
                  <span
                    className="chip chip-amber"
                    title="claim won; an observational metric regressed"
                  >
                    pareto tradeoff
                  </span>
                )}
              </div>

              <div className="battle-meta muted">
                <span className="font-mono">{bt.battle_id}</span>
                <span> · seed {bt.seed ?? "—"}</span>
                <span> · {bt.task_count ?? "—"} tasks</span>
                {bt.ledger_ts && (
                  <span>
                    {" "}
                    · {bt.ledger_ts.slice(0, 16).replace("T", " ")}
                  </span>
                )}
              </div>

              {bt.measured && (
                <div className="metrics-row">
                  {Object.entries(bt.measured).map(([m, d]) => {
                    const isPos = d.delta > 0;
                    const isNeg = d.delta < 0;
                    return (
                      <span
                        key={m}
                        className={`metric ${
                          isPos ? "delta-pos" : isNeg ? "delta-neg" : ""
                        }`}
                        title={`baseline ${d.baseline} → candidate ${d.candidate} (n=${d.n})`}
                      >
                        <span>{m}:</span>
                        <b>
                          {isPos ? "+" : ""}
                          {d.delta}
                        </b>
                      </span>
                    );
                  })}
                </div>
              )}

              {amendments.map((a, i) => (
                <div key={i} className="amendment font-mono">
                  <IconAmendment
                    size={14}
                    style={{ color: "var(--rad-amber)", flexShrink: 0 }}
                  />
                  <span>
                    amended: <b>{a.was}</b> → <b>{a.now}</b> — {a.reason}
                  </span>
                  {a.amended_at && (
                    <span className="hint" style={{ marginLeft: "auto" }}>
                      {a.amended_at.slice(0, 16).replace("T", " ")}
                    </span>
                  )}
                </div>
              ))}
            </article>
          );
        })}
      </div>
    </div>
  );
}

function LedgerSkeleton() {
  return (
    <div className="page" aria-busy="true">
      <div className="page-header">
        <div className="page-title-group" style={{ width: "300px" }}>
          <Skeleton height={24} width="200px" style={{ marginBottom: 6 }} />
          <Skeleton height={14} width="280px" />
        </div>
      </div>
      <div className="ledger-head">
        <Skeleton height={20} width="100px" />
        <Skeleton height={20} width="160px" />
        <Skeleton height={20} width="120px" />
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="battle-card">
            <div style={{ display: "flex", gap: 10 }}>
              <Skeleton height={22} width="110px" radius="var(--radius-pill)" />
              <Skeleton height={22} width="240px" />
            </div>
            <Skeleton height={14} width="320px" />
            <div style={{ display: "flex", gap: 8 }}>
              <Skeleton height={24} width="90px" />
              <Skeleton height={24} width="90px" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

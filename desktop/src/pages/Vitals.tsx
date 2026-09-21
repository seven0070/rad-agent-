// Vitals.tsx — the organism's cockpit page.
// Three glance-zones: PULSE (homeostasis) · WONDER (curiosity) · SHIELD (canary).
// Law: behavior only; every empty state honest; "configured-to", never "alive".

import { useCallback, useEffect, useState } from "react";
import { useRad } from "../ctx";
import {
  IconVitals,
  IconCompass,
  IconShield,
  IconAlert,
  IconCheck,
  IconRefresh,
} from "../components/Icons";
import { Skeleton } from "../components/Skeleton";

export type VitalsData = {
  vitals: {
    memory_organ: { present: boolean; note: string };
    digestion_organ: { papers_ingested: number; battles_ledgered: number };
    sovereignty: number | null;
    life_refusal_law: string[];
  };
  human: string;
  curiosity: {
    report: string;
    last: { pick: { slug: string } | null; open_question: string | null } | null;
  };
  cadence: { ran_at: string; verdict: string; battery_healthy?: boolean } | null;
};

export default function Vitals() {
  const { client } = useRad();
  const [d, setD] = useState<VitalsData | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (showRefreshing = false) => {
    if (showRefreshing) setRefreshing(true);
    try {
      let resData: VitalsData;
      if (client) {
        resData = await client.vitals<VitalsData>();
      } else {
        const res = await fetch("/api/vitals");
        if (!res.ok) throw new Error(`sidecar ${res.status}`);
        resData = await res.json();
      }
      setD(resData);
      setErr(null);
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
      if (showRefreshing) setRefreshing(false);
    }
  }, [client]);

  useEffect(() => {
    let alive = true;
    const fetchOrgans = async () => {
      if (alive) await load();
    };
    void fetchOrgans();
    const t = setInterval(fetchOrgans, 30_000); // organs change at sleep-time, not per-keystroke
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, [load]);

  if (err && !d) {
    return (
      <div className="page" role="region" aria-label="Organ Vitals">
        <div className="page-header">
          <div className="page-title-group">
            <h2>
              <IconVitals size={20} style={{ color: "var(--rad-indigo)" }} />
              Vitals
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

  if (loading && !d) {
    return <VitalsSkeleton />;
  }

  if (!d) return null;

  const v = d.vitals;
  const canary = d.cadence;
  const sovPct = v.sovereignty == null ? null : Math.round(v.sovereignty * 100);

  return (
    <div className="page" role="region" aria-label="Organ Vitals">
      {/* Page Header */}
      <div className="page-header">
        <div className="page-title-group">
          <h2>
            <IconVitals size={20} style={{ color: "var(--rad-indigo)" }} />
            Vitals
          </h2>
          <p className="lead">{d.human}</p>
        </div>
        <button
          className="btn ghost mini"
          onClick={() => void load(true)}
          disabled={refreshing}
          aria-label="Refresh organ state"
        >
          <IconRefresh
            size={12}
            className={refreshing ? "spin" : ""}
            style={{ marginRight: 5 }}
          />
          {refreshing ? "Polling…" : "Check Organs"}
        </button>
      </div>

      <div className="vitals-grid">
        {/* Zone 1: PULSE (Homeostasis) */}
        <section className="vitals-zone zone-pulse" aria-labelledby="zone-pulse-title">
          <div className="vitals-zone-header">
            <div className="vitals-zone-title" id="zone-pulse-title">
              <IconVitals size={14} style={{ color: "var(--rad-indigo)" }} />
              Pulse · Homeostasis
            </div>
            <span className="vitals-zone-pill">Organ Balance</span>
          </div>

          <div className="vitals-metrics-grid">
            {/* Memory Organ */}
            <div className="vitals-metric-card" title={v.memory_organ.note}>
              <span className="vitals-metric-label">Memory Organ</span>
              <div className="vitals-metric-value">
                <span
                  className={`chip ${
                    v.memory_organ.present ? "chip-green" : "chip-amber"
                  }`}
                  style={{ padding: "1px 6px" }}
                >
                  <span
                    className="dot"
                    style={{
                      backgroundColor: v.memory_organ.present
                        ? "var(--emerald-verif)"
                        : "var(--rad-amber)",
                      width: 6,
                      height: 6,
                    }}
                  />
                  {v.memory_organ.present ? "Active" : "Absent"}
                </span>
              </div>
              <span className="vitals-metric-sub">{v.memory_organ.note}</span>
            </div>

            {/* Ingested Papers */}
            <div className="vitals-metric-card">
              <span className="vitals-metric-label">Papers Ingested</span>
              <div className="vitals-metric-value tabular-nums">
                {v.digestion_organ.papers_ingested}
              </div>
              <span className="vitals-metric-sub">arXiv ingested & parsed</span>
            </div>

            {/* Battles Ledgered */}
            <div className="vitals-metric-card">
              <span className="vitals-metric-label">Battles Ledgered</span>
              <div className="vitals-metric-value tabular-nums">
                {v.digestion_organ.battles_ledgered}
              </div>
              <span className="vitals-metric-sub">Replication runs on record</span>
            </div>

            {/* Sovereignty */}
            <div className="vitals-metric-card">
              <span className="vitals-metric-label">Sovereignty</span>
              <div className="vitals-metric-value tabular-nums">
                {sovPct == null ? (
                  <span style={{ fontSize: 13, color: "var(--text-muted)", fontWeight: 500 }}>
                    no events yet
                  </span>
                ) : (
                  `${sovPct}% internal`
                )}
              </div>
              <span className="vitals-metric-sub">Internal decision ratio</span>
            </div>
          </div>
        </section>

        {/* Zone 2: WONDER (Curiosity) */}
        <section className="vitals-zone zone-wonder" aria-labelledby="zone-wonder-title">
          <div className="vitals-zone-header">
            <div className="vitals-zone-title" id="zone-wonder-title">
              <IconCompass size={14} style={{ color: "var(--rad-amber)" }} />
              Wonder · Curiosity Drive
            </div>
            <span className="vitals-zone-pill">Autonomous Exploration</span>
          </div>

          {!d.curiosity.last || !d.curiosity.last.pick ? (
            <div className="vitals-rest-banner">
              <span className="dot" style={{ backgroundColor: "var(--text-dim)", width: 6, height: 6 }} />
              <span>nothing unexplored — honest rest</span>
            </div>
          ) : (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 8,
                background: "rgba(9, 10, 15, 0.6)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                padding: "12px 14px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <span className="hint">Last Exploration:</span>
                <code
                  className="font-mono"
                  style={{
                    color: "var(--rad-amber)",
                    background: "rgba(245, 158, 11, 0.1)",
                    padding: "2px 8px",
                    borderRadius: 4,
                    border: "1px solid rgba(245, 158, 11, 0.25)",
                    fontSize: 12,
                  }}
                >
                  {d.curiosity.last.pick.slug}
                </code>
              </div>
              {d.curiosity.last.open_question && (
                <div style={{ fontSize: 13, color: "var(--text-secondary)", fontStyle: "italic", lineHeight: 1.5 }}>
                  “{d.curiosity.last.open_question}”
                </div>
              )}
            </div>
          )}
        </section>

        {/* Zone 3: SHIELD (Canary Cadence) */}
        <section
          className={`vitals-zone zone-shield ${
            canary?.battery_healthy === false ? "shield-compromised" : ""
          }`}
          aria-labelledby="zone-shield-title"
        >
          <div className="vitals-zone-header">
            <div className="vitals-zone-title" id="zone-shield-title">
              <IconShield
                size={14}
                style={{
                  color:
                    canary?.battery_healthy === false
                      ? "var(--rose-danger)"
                      : "var(--emerald-verif)",
                }}
              />
              Shield · Canary Cadence
            </div>
            <span className="vitals-zone-pill">Battery & Promotion Gate</span>
          </div>

          {!canary ? (
            <div className="vitals-rest-banner">
              <span className="dot" style={{ backgroundColor: "var(--text-dim)", width: 6, height: 6 }} />
              <span>no canary run on record yet — first sleep schedules one</span>
            </div>
          ) : canary.battery_healthy === false ? (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "12px 14px",
                background: "rgba(244, 63, 94, 0.08)",
                border: "1px solid rgba(244, 63, 94, 0.3)",
                borderRadius: "var(--radius-sm)",
                color: "var(--rose-danger)",
                fontSize: 13,
              }}
            >
              <IconAlert size={16} />
              <span>
                Battery integrity: <b>{canary.verdict}</b> — promotion gates closed
              </span>
            </div>
          ) : (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "12px 14px",
                background: "rgba(9, 10, 15, 0.6)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-sm)",
                fontSize: 13,
                flexWrap: "wrap",
                gap: 8,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <IconCheck size={16} style={{ color: "var(--emerald-verif)" }} />
                <span>Canary healthy</span>
              </div>
              <span className="hint font-mono tabular-nums">
                last ran: {canary.ran_at.slice(0, 16).replace("T", " ")}
              </span>
            </div>
          )}
        </section>
      </div>

      {/* Life Refusal Law: strictly preserved, behavioral dignity */}
      <footer className="life-refusal-banner">
        {v.life_refusal_law.join(" · ")}
      </footer>
    </div>
  );
}

function VitalsSkeleton() {
  return (
    <div className="page" aria-busy="true">
      <div className="page-header">
        <div className="page-title-group" style={{ width: "240px" }}>
          <Skeleton height={24} width="140px" style={{ marginBottom: 6 }} />
          <Skeleton height={14} width="220px" />
        </div>
      </div>
      <div className="vitals-grid">
        <div className="vitals-zone zone-pulse">
          <Skeleton height={14} width="160px" style={{ marginBottom: 14 }} />
          <div className="vitals-metrics-grid">
            <Skeleton height={68} radius="var(--radius-sm)" />
            <Skeleton height={68} radius="var(--radius-sm)" />
            <Skeleton height={68} radius="var(--radius-sm)" />
            <Skeleton height={68} radius="var(--radius-sm)" />
          </div>
        </div>
        <div className="vitals-zone zone-wonder">
          <Skeleton height={14} width="180px" style={{ marginBottom: 14 }} />
          <Skeleton height={52} radius="var(--radius-sm)" />
        </div>
        <div className="vitals-zone zone-shield">
          <Skeleton height={14} width="170px" style={{ marginBottom: 14 }} />
          <Skeleton height={52} radius="var(--radius-sm)" />
        </div>
      </div>
    </div>
  );
}

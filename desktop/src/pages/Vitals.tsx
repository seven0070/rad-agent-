// Vitals.tsx — the organism's cockpit page.
// Three glance-zones: PULSE (homeostasis) · WONDER (curiosity) · SHIELD (canary).
// Law: behavior only; every empty state honest; "configured-to", never "alive".

import { useCallback, useEffect, useState } from "react";
import { RadClient } from "../api";
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
      const c = client || new RadClient("", "");
      const resData: VitalsData = await c.vitals<VitalsData>();
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
              <IconVitals size={20} className="icon-indigo" />
              Vitals
            </h2>
            <p className="lead">Sidecar unreachable</p>
          </div>
          <button className="btn ghost" onClick={() => void load(true)}>
            <IconRefresh size={13} className="mr-6" />
            Retry
          </button>
        </div>
        <div className="card card-alert">
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
            <IconVitals size={20} className="icon-indigo" />
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
            className={refreshing ? "spin mr-5" : "mr-5"}
          />
          {refreshing ? "Polling…" : "Check Organs"}
        </button>
      </div>

      <div className="vitals-grid">
        {/* Zone 1: PULSE (Homeostasis) */}
        <section className="vitals-zone zone-pulse" aria-labelledby="zone-pulse-title">
          <div className="vitals-zone-header">
            <div className="vitals-zone-title" id="zone-pulse-title">
              <IconVitals size={14} className="icon-indigo" />
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
                  className={`chip pad-1-6 ${
                    v.memory_organ.present ? "chip-green" : "chip-amber"
                  }`}
                >
                  <span
                    className="dot dot-6"
                    style={{
                      backgroundColor: v.memory_organ.present
                        ? "var(--emerald-verif)"
                        : "var(--rad-amber)",
                    }} // DYNAMIC-STYLE: present/absent dot color
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
                  <span className="fs-13 tc-muted fw-500">
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
              <IconCompass size={14} className="icon-amber" />
              Wonder · Curiosity Drive
            </div>
            <span className="vitals-zone-pill">Autonomous Exploration</span>
          </div>

          {!d.curiosity.last || !d.curiosity.last.pick ? (
            <div className="vitals-rest-banner">
              <span className="dot dot-6 dot-dim" />
              <span>nothing unexplored — honest rest</span>
            </div>
          ) : (
            <div className="panel-block">
              <div className="flex-mid gap-8 flex-wrap">
                <span className="hint">Last Exploration:</span>
                <code className="font-mono slug-code">
                  {d.curiosity.last.pick.slug}
                </code>
              </div>
              {d.curiosity.last.open_question && (
                <div className="open-question">
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
                className={
                  canary?.battery_healthy === false ? "tc-danger" : "icon-verif"
                }
              />
              Shield · Canary Cadence
            </div>
            <span className="vitals-zone-pill">Battery & Promotion Gate</span>
          </div>

          {!canary ? (
            <div className="vitals-rest-banner">
              <span className="dot dot-6 dot-dim" />
              <span>no canary run on record yet — first sleep schedules one</span>
            </div>
          ) : canary.battery_healthy === false ? (
            <div className="panel-row-danger">
              <IconAlert size={16} />
              <span>
                Battery integrity: <b>{canary.verdict}</b> — promotion gates closed
              </span>
            </div>
          ) : (
            <div className="panel-row">
              <div className="flex-mid gap-8">
                <IconCheck size={16} className="icon-verif" />
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
        <div className="page-title-group w-240">
          <Skeleton height={24} width="140px" className="mb-6" />
          <Skeleton height={14} width="220px" />
        </div>
      </div>
      <div className="vitals-grid">
        <div className="vitals-zone zone-pulse">
          <Skeleton height={14} width="160px" className="mb-14" />
          <div className="vitals-metrics-grid">
            <Skeleton height={68} radius="var(--radius-sm)" />
            <Skeleton height={68} radius="var(--radius-sm)" />
            <Skeleton height={68} radius="var(--radius-sm)" />
            <Skeleton height={68} radius="var(--radius-sm)" />
          </div>
        </div>
        <div className="vitals-zone zone-wonder">
          <Skeleton height={14} width="180px" className="mb-14" />
          <Skeleton height={52} radius="var(--radius-sm)" />
        </div>
        <div className="vitals-zone zone-shield">
          <Skeleton height={14} width="170px" className="mb-14" />
          <Skeleton height={52} radius="var(--radius-sm)" />
        </div>
      </div>
    </div>
  );
}

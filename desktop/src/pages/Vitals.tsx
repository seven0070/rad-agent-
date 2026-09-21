// Vitals.tsx — the organism's cockpit page.
// Three glance-zones: PULSE (homeostasis) · WONDER (curiosity) · SHIELD (canary).
// Law: behavior only; every empty state honest; "configured-to", never "alive".

import { useEffect, useState } from "react";
import { useRad } from "../ctx";

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

  useEffect(() => {
    let alive = true;
    const load = async () => {
      try {
        let resData: VitalsData;
        if (client) {
          resData = await client.vitals<VitalsData>();
        } else {
          const res = await fetch("/api/vitals");
          if (!res.ok) throw new Error(`sidecar ${res.status}`);
          resData = await res.json();
        }
        if (alive) { setD(resData); setErr(null); }
      } catch (e) { if (alive) setErr(String(e)); }
    };
    load();
    const t = setInterval(load, 30_000);   // organs change at sleep-time, not per-keystroke
    return () => { alive = false; clearInterval(t); };
  }, [client]);

  if (err) return <div className="page"><h2>Vitals</h2><p className="muted">sidecar unreachable: {err}</p></div>;
  if (!d) return <div className="page"><h2>Vitals</h2><p className="muted">reading organs…</p></div>;

  const v = d.vitals;
  const canary = d.cadence;

  return (
    <div className="page">
      <h2>Vitals</h2>
      <p className="muted">{d.human}</p>

      <div className="vitals-zone">
        <h3>Pulse</h3>
        <div className="metrics-row">
          <span className="metric" title={v.memory_organ.note}>
            memory: {v.memory_organ.present ? "on" : "absent"}
          </span>
          <span className="metric">papers: {v.digestion_organ.papers_ingested}</span>
          <span className="metric">battles: {v.digestion_organ.battles_ledgered}</span>
          <span className="metric">
            sovereignty: {v.sovereignty == null ? "no events yet"
                          : `${Math.round(v.sovereignty * 100)}% internal`}
          </span>
        </div>
      </div>

      <div className="vitals-zone">
        <h3>Wonder</h3>
        {!d.curiosity.last || !d.curiosity.last.pick ? (
          <p className="muted">nothing unexplored — honest rest</p>
        ) : (
          <p>
            last exploration: <code>{d.curiosity.last.pick.slug}</code>
            {d.curiosity.last.open_question && (
              <span className="muted"> — “{d.curiosity.last.open_question}”</span>
            )}
          </p>
        )}
      </div>

      <div className="vitals-zone">
        <h3>Shield</h3>
        {!canary ? (
          <p className="muted">no canary run on record yet — first sleep schedules one</p>
        ) : canary.battery_healthy === false ? (
          <p style={{ color: "#c62828" }}>
            ⚠ battery integrity: {canary.verdict} — promotion gates closed
          </p>
        ) : (
          <p>canary healthy · last ran <code>{canary.ran_at.slice(0, 16).replace("T", " ")}</code></p>
        )}
      </div>

      <p className="muted" style={{ fontSize: "0.8em", marginTop: "1.5rem" }}>
        {v.life_refusal_law.join(" · ")}
      </p>
    </div>
  );
}

/** Memory viewer over the existing /v1/memory + /v1/memory/recall. */
import { useCallback, useEffect, useState } from "react";
import { ApiError, MemoryRow } from "../api";
import { useRad } from "../ctx";
import { fmtTime, redactText } from "../util";

const LAYERS = ["working", "episodic", "semantic", "procedural"];

export default function Memory() {
  const { client } = useRad();
  const [q, setQ] = useState("");
  const [recall, setRecall] = useState<MemoryRow[]>([]);
  const [listing, setListing] = useState<Record<string, MemoryRow[]>>({});
  const [active, setActive] = useState<string>("all");
  const [remember, setRemember] = useState("");
  const [layer, setLayer] = useState("semantic");
  const [err, setErr] = useState("");
  const [ok, setOk] = useState("");

  const load = useCallback(async () => {
    try {
      const l = active === "all" ? undefined : active;
      const r = await client.memory(l, 100);
      setListing(r.memories);
      setErr("");
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    }
  }, [client, active]);

  useEffect(() => {
    void load();
    const t = setInterval(load, 15000);
    return () => clearInterval(t);
  }, [load]);

  const doRecall = async () => {
    const term = q.trim();
    if (!term) return;
    try {
      const r = await client.recall(term, 10);
      setRecall(r.memories);
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    }
  };

  const doRemember = async () => {
    const t = remember.trim();
    if (!t) return;
    try {
      await client.remember(t, layer);
      setRemember("");
      setOk("remembered (origin USER_PROVIDED, source api)");
      void load();
    } catch (e) {
      setErr(e instanceof ApiError ? e.message : String(e));
    }
  };

  const shown =
    q.trim() && recall.length
      ? recall
      : active === "all"
        ? LAYERS.flatMap((l) => listing[l] || [])
        : listing[active] || [];

  return (
    <div>
      <h1>Memory</h1>
      <p className="lead">
        Human-inspired memory (origin, confidence, verification state). Entries are
        provenance-tracked; contradictions are linked, not merged.
      </p>

      <div className="card">
        <div className="row">
          <input
            placeholder="search memories (recall)"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void doRecall()}
          />
          <button className="btn" onClick={() => void doRecall()}>
            Recall
          </button>
        </div>
        <div className="row" style={{ marginTop: 10 }}>
          {["all", ...LAYERS].map((l) => (
            <button
              key={l}
              className={`btn mini ${active === l ? "" : "ghost"}`}
              onClick={() => setActive(l)}
            >
              {l}
              {listing[l] ? ` (${listing[l].length})` : ""}
            </button>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="row">
          <input
            placeholder="store a memory (origin: USER_PROVIDED)"
            value={remember}
            onChange={(e) => setRemember(e.target.value)}
          />
          <select value={layer} onChange={(e) => setLayer(e.target.value)} style={{ width: 130 }}>
            {["episodic", "semantic", "procedural"].map((l) => (
              <option key={l}>{l}</option>
            ))}
          </select>
          <button className="btn" onClick={() => void doRemember()}>
            Remember
          </button>
        </div>
        {ok && <p className="ok">{ok}</p>}
        {err && <p className="err">{err}</p>}
      </div>

      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>layer</th>
                <th>text</th>
                <th>origin</th>
                <th>confidence</th>
                <th>verification</th>
                <th>strength</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((m) => (
                <tr key={m.id}>
                  <td className="hint">{m.layer}</td>
                  <td style={{ maxWidth: 480 }}>{redactText(m.text).slice(0, 240)}</td>
                  <td className="hint">{m.origin}</td>
                  <td className="hint">{m.confidence.toFixed ? m.confidence.toFixed(2) : m.confidence}</td>
                  <td>
                    <span
                      className={`badge ${
                        m.verification === "VERIFIED" ? "b-ok" : m.verification === "CONTRADICTED" ? "b-bad" : "b-warn"
                      }`}
                    >
                      {m.verification || "UNVERIFIED"}
                    </span>
                  </td>
                  <td className="hint">{fmtTime(m.strength as unknown as number) === "—" ? String(m.strength) : String(m.strength)}</td>
                </tr>
              ))}
              {shown.length === 0 && (
                <tr>
                  <td colSpan={6} className="hint">
                    no memories{q ? ` for “${q}”` : ""}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

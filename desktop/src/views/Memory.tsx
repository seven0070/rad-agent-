import { useEffect, useState } from "react";
import { MemoryLayer, MemoryRow, RadClient } from "../api";

function chipClass(v: string | undefined) {
  return `chip ${(v || "pending").toLowerCase()}`;
}

const LAYERS: MemoryLayer[] = ["episodic", "semantic", "procedural"];

/**
 * Recall + add memories through the RadClient. Recall is a plain request;
 * results are rendered read-only.
 */
export function Memory({ client }: { client: RadClient }) {
  const [rows, setRows] = useState<MemoryRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [q, setQ] = useState("");
  const [k, setK] = useState(5);
  const [layer, setLayer] = useState<MemoryLayer>("semantic");
  const [text, setText] = useState("");
  const [created, setCreated] = useState<MemoryRow | null>(null);

  const runRecall = async (query: string, kn: number) => {
    const kk = Math.min(50, Math.max(1, Math.floor(kn) || 1));
    setBusy(true);
    setErr("");
    try {
      const r = await client.memoryRecall(query, kk);
      setRows(r.memories);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    let live = true;
    client
      .memoryRecall("", 5)
      .then((r) => {
        if (live) setRows(r.memories);
      })
      .catch(() => {});
    return () => {
      live = false;
    };
  }, [client]);

  const add = async () => {
    const t = text.trim();
    if (!t) return;
    setErr("");
    try {
      const row = await client.memoryAdd(t, layer);
      setCreated(row);
      setText("");
      void runRecall(q, k);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div>
      <h1>Memory</h1>
      <p className="lead">
        Recall and add from the control plane's memory store. Existing memories are rendered
        read-only with their reported origin and confidence.
      </p>
      {err && <p className="err">{err}</p>}
      <div className="card">
        <h3>Add</h3>
        <label>Layer</label>
        <select value={layer} onChange={(e) => setLayer(e.target.value as MemoryLayer)}>
          {LAYERS.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
        <label style={{ marginTop: 10 }}>Text</label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="memory to store"
        />
        <div className="row" style={{ marginTop: 10 }}>
          <button className="btn" onClick={() => void add()}>
            Add
          </button>
        </div>
        {created && (
          <div className="kv" style={{ marginTop: 10 }}>
            <div className="kv-row">
              <span className="k">stored</span>
              <span className="v mono">{created.id.slice(0, 12)}</span>
            </div>
            <div className="kv-row">
              <span className="k">origin</span>
              <span className="v">
                <span className={chipClass(created.origin || "USER_PROVIDED")}>
                  {created.origin || "USER_PROVIDED"}
                </span>
              </span>
            </div>
            <div className="kv-row">
              <span className="k">layer</span>
              <span className="v">
                <span className={chipClass(created.layer)}>{created.layer}</span>
              </span>
            </div>
            <div className="kv-row">
              <span className="k">text</span>
              <span className="v">{created.text}</span>
            </div>
          </div>
        )}
      </div>
      <div className="card">
        <h3>Recall</h3>
        <div className="row">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="query (empty = recent)"
            style={{ flex: 1, minWidth: 200 }}
          />
          <input
            type="number"
            value={k}
            min={1}
            max={50}
            onChange={(e) => setK(Number(e.target.value))}
            style={{ width: 80 }}
            title="k (1..50)"
          />
          <button className="btn" disabled={busy} onClick={() => void runRecall(q, k)}>
            Recall
          </button>
        </div>
        {rows.length === 0 && !busy && <p className="meta" style={{ marginTop: 10 }}>no memories returned</p>}
        {rows.map((m) => (
          <div key={m.id} className="check" style={{ marginTop: 8 }}>
            <span className={chipClass(m.layer)}>{m.layer}</span>
            <div style={{ flex: 1 }}>
              <div>{m.text}</div>
              <div className="meta">
                {m.origin} · confidence {m.confidence} · strength {m.strength}
                {m.verification ? ` · ${m.verification}` : ""}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
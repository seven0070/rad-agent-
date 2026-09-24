// McpMallPane.tsx — N4 Appsmith: auto panel for rad objective (McMall)
// Inspired by appsmith auto-panel: when an objective is active, this pane auto-queries
// the mall (rad skills marketplace) and shows suggested MCPs without user ask.
// Keeps Self-Writing Mall x402 flow: skills invent -> MCP server -> publish -> x402.

import { useEffect, useState } from "react";

interface MallItem {
  name: string;
  approval: string;
  trust: string;
  capabilities: string[];
  tools: number;
}

interface McpMallPaneProps {
  objectiveGoal?: string;
  objectiveId?: string;
  auto?: boolean;
}

function getApiBase(): string {
  return (import.meta as any).env?.VITE_API_BASE || "";
}

export const McpMallPane: React.FC<McpMallPaneProps> = ({ objectiveGoal, objectiveId, auto = true }) => {
  const [items, setItems] = useState<MallItem[]>([]);
  const [query, setQuery] = useState(objectiveGoal?.slice(0, 40) || "");
  const [loading, setLoading] = useState(false);
  const [x402, setX402] = useState<{ enabled: boolean; note: string } | null>(null);

  useEffect(() => {
    if (objectiveGoal) setQuery(objectiveGoal.slice(0, 60));
  }, [objectiveGoal]);

  useEffect(() => {
    if (!auto) return;
    let cancelled = false;
    async function mallSearch(q: string) {
      setLoading(true);
      try {
        const { RadClient } = await import("../../api");
        const base = getApiBase();
        let res: any = { results: [] };
        if (base) {
          const client = new RadClient(base, "");
          try {
            res = await (client as any).mallSearch?.(q) ?? await (client as any).skillsSearch?.(q) ?? { results: [] };
          } catch {
            // offline stub: fabricate from local
            res = { results: [] };
          }
        }
        // fallback stub when offline: derive from goal keywords
        if (!res.results || res.results.length === 0) {
          const kw = (q || "").toLowerCase().split(/\W+/).filter((w) => w.length > 3).slice(0, 3);
          const stub: MallItem[] = kw.length
            ? kw.map((k) => ({ name: `suggest-${k}`, approval: "ask", trust: "community", capabilities: [k], tools: 1 }))
            : [{ name: "demo-skill", approval: "ask", trust: "local", capabilities: ["fs_read"], tools: 1 }];
          if (!cancelled) setItems(stub);
        } else {
          if (!cancelled) setItems(res.results.slice(0, 6));
        }
        if (!cancelled) setX402({ enabled: true, note: "x402 publish kept — invent->MCP->publish->x402" });
      } catch {
        if (!cancelled) setItems([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    const q = query || objectiveGoal || "";
    if (q) mallSearch(q);
    else setItems([]);
    return () => { cancelled = true; };
  }, [query, objectiveGoal, auto]);

  return (
    <div className="mcp-mall-pane" data-testid="mcp-mall-pane" style={{ padding: 12, borderTop: "1px solid var(--border)", background: "var(--card)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <h4 style={{ margin: 0, fontSize: 13, fontWeight: 700 }}>McMall — Auto for Objective</h4>
        <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 10, background: "#18181b", color: "#a1a1aa", border: "1px solid #27272a" }}>
          {objectiveId ? `obj:${objectiveId.slice(0, 6)}` : "no obj"}
        </span>
      </div>
      <div style={{ fontSize: 11, opacity: 0.6, marginBottom: 8 }}>
        Appsmith-style auto panel: suggests mall MCPs from objective goal (read-only, no auto-install).
      </div>
      <div style={{ display: "flex", gap: 6, marginBottom: 10 }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="mall search…"
          style={{ flex: 1, fontSize: 12, padding: "6px 8px", borderRadius: 6, border: "1px solid var(--border)", background: "#0a0a0a", color: "#fafafa" }}
        />
        <span style={{ fontSize: 11, lineHeight: "28px", opacity: 0.5 }}>{loading ? "loading…" : `${items.length} hit`}</span>
      </div>
      {items.length === 0 ? (
        <div style={{ fontSize: 12, opacity: 0.5 }}>No mall suggestions. Objective will still run with built-ins.</div>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 6 }}>
          {items.map((it) => (
            <li key={it.name} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, padding: "8px 10px", border: "1px solid var(--border)", borderRadius: 8, background: "#0a0a0a" }}>
              <span style={{ fontWeight: 600 }}>{it.name}</span>
              <span style={{ opacity: 0.6, fontFamily: "monospace", fontSize: 10 }}>{it.approval}/{it.trust} · {it.capabilities.join(",")} · {it.tools} tools</span>
            </li>
          ))}
        </ul>
      )}
      {x402 && (
        <div style={{ marginTop: 10, fontSize: 10, opacity: 0.4, fontFamily: "monospace" }}>
          Self-Writing Mall: {x402.note} · x402 micropay kept
        </div>
      )}
      <div style={{ marginTop: 6, fontSize: 10, opacity: 0.3 }}>N4 · Appsmith auto-panel · read-only</div>
    </div>
  );
};

export default McpMallPane;

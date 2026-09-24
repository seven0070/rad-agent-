import React, { useEffect, useState } from "react";

interface McpPlugin {
  name: string;
  transport: string;
  approval: string;
  capabilities: string[];
  tools: number;
}

interface GgufStatus {
  supported: boolean;
  reason: string;
  gguf_models: string[];
}

// P0 stub: observability only via RadClient (keeps network inside api.ts per desktop security surface)
function getApiBase(): string {
  // Tauri dev: vite proxy or direct loopback; fallback to relative for web
  return (import.meta as any).env?.VITE_API_BASE || "";
}

export const McpPluginPane: React.FC = () => {
  const [plugins, setPlugins] = useState<McpPlugin[]>([]);
  const [gguf, setGguf] = useState<GgufStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      // P1 stub: use api.ts client shape when available, otherwise offline stub
      // Direct fetch intentionally avoided here — must go through api.ts RadClient
      try {
        // Lazy import to avoid cycle; api.ts owns the network call
        const { RadClient } = await import("../../api");
        const base = getApiBase();
        // Token not needed for P0 offline stub (shows empty) — real data when desktop bundles token
        let skillsRes: any = { skills: [] };
        let providersRes: any = { providers: [] };
        if (base) {
          const client = new RadClient(base, "");
          try { skillsRes = await client.skillsManifest(); } catch { /* offline stub */ }
          try { providersRes = await client.providersHealth(); } catch { /* offline stub */ }
        }
        if (cancelled) return;
        const list: McpPlugin[] = Array.isArray(skillsRes.skills) ? skillsRes.skills : Array.isArray(skillsRes) ? skillsRes : [];
        setPlugins(list);
        const providers: any[] = providersRes.providers || [];
        const ollama = providers.find((p: any) => p.name === "ollama");
        if (ollama) {
          const ggufModels: string[] = (ollama as any)._gguf_models || ollama.gguf_models || [];
          const supported = (ollama as any)._gguf_supported ?? true;
          setGguf({ supported, reason: ollama.health || "ollama GGUF import via ollama create", gguf_models: ggufModels });
        } else {
          setGguf({ supported: true, reason: "ollama GGUF import stub (offline)", gguf_models: [] });
        }
      } catch {
        if (!cancelled) setGguf({ supported: false, reason: "probe failed", gguf_models: [] });
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return <div className="mcp-plugin-pane loading">Loading plugins...</div>;
  }

  return (
    <div className="mcp-plugin-pane" data-testid="mcp-plugin-pane" style={{ padding: 12, borderTop: "1px solid var(--border)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
        <h4 style={{ margin: 0, fontSize: 13, fontWeight: 600 }}>MCP Plugins</h4>
        <span style={{ fontSize: 11, opacity: 0.6 }}>{plugins.length} connected</span>
      </div>
      {plugins.length === 0 ? (
        <div style={{ fontSize: 12, opacity: 0.6 }}>No MCP plugins connected. Run rad connect to add one.</div>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "grid", gap: 6 }}>
          {plugins.map((p) => (
            <li key={p.name} style={{ display: "flex", justifyContent: "space-between", fontSize: 12, padding: "6px 8px", border: "1px solid var(--border)", borderRadius: 6 }}>
              <span style={{ fontWeight: 500 }}>{p.name}</span>
              <span style={{ opacity: 0.6 }}>{p.approval || "policy"} - {p.capabilities?.join(",") || "mcp"}</span>
            </li>
          ))}
        </ul>
      )}
      <div style={{ marginTop: 12, padding: 8, border: "1px dashed var(--border)", borderRadius: 6 }}>
        <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Ollama GGUF Import</div>
        <div style={{ fontSize: 11, opacity: 0.7 }}>{gguf?.reason || "detecting..."}</div>
        {gguf?.gguf_models && gguf.gguf_models.length > 0 ? (
          <ul style={{ fontSize: 11, margin: "4px 0 0 12px" }}>
            {gguf.gguf_models.map((m) => <li key={m}>{m}</li>)}
          </ul>
        ) : (
          <div style={{ fontSize: 11, opacity: 0.5, marginTop: 4 }}>No GGUF models detected - import via ollama create (GGUF path)</div>
        )}
        <div style={{ fontSize: 10, opacity: 0.4, marginTop: 6 }}>P1 stub: probe_local GGUF detection (observability only)</div>
      </div>
    </div>
  );
};

export default McpPluginPane;

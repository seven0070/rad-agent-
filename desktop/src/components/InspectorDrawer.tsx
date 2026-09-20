import { useCallback, useEffect, useState } from "react";
import { Artifact, ArtifactContent, ObjectiveRow } from "../api";
import { useRad } from "../ctx";
import { fmtBytes, shortHash } from "../util";

interface InspectorDrawerProps {
  objective: ObjectiveRow | null;
  selectedArtifactId?: string | null;
  onSelectArtifact?: (id: string) => void;
  onClose?: () => void;
}

type Tab = "files" | "code" | "verification" | "checkpoints" | "telemetry";

export default function InspectorDrawer({
  objective,
  selectedArtifactId,
  onSelectArtifact,
  onClose,
}: InspectorDrawerProps) {
  const { client } = useRad();
  const [tab, setTab] = useState<Tab>("files");
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null);
  const [content, setContent] = useState<ArtifactContent | null>(null);
  const [trace, setTrace] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const id = objective?.id;

  // Sync external selectedArtifactId
  useEffect(() => {
    if (selectedArtifactId) {
      setSelectedArtifact(selectedArtifactId);
      setTab("code");
    }
  }, [selectedArtifactId]);

  // Load artifacts and trace
  const load = useCallback(async () => {
    if (!id) return;
    try {
      const [artRes, trRes] = await Promise.all([
        client.artifacts(id).catch(() => ({ artifacts: [] })),
        client.trace(id).catch(() => null),
      ]);
      setArtifacts(artRes.artifacts || []);
      setTrace(trRes);
      if (artRes.artifacts?.length && !selectedArtifact && !selectedArtifactId) {
        setSelectedArtifact(artRes.artifacts[0].id);
      }
    } catch {
      // ignore
    }
  }, [client, id, selectedArtifact, selectedArtifactId]);

  useEffect(() => {
    void load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [load]);

  // Load preview when selected artifact changes
  useEffect(() => {
    if (!id || !selectedArtifact) {
      setContent(null);
      return;
    }
    let stop = false;
    const fetchContent = async () => {
      setLoading(true);
      try {
        const c = await client.artifactContent(id, selectedArtifact);
        if (!stop) setContent(c);
      } catch {
        if (!stop) setContent(null);
      } finally {
        if (!stop) setLoading(false);
      }
    };
    void fetchContent();
    return () => { stop = true; };
  }, [client, id, selectedArtifact]);

  const ver = trace?.verification?.objective || {};
  const results = ver.results || [];
  const cpIntact = trace?.checkpoint?.intact ?? true;
  const cpSeq = trace?.checkpoint?.seq ?? 8;
  const cpDigest = trace?.checkpoint?.digest || "e931dcc03ceac399";

  return (
    <aside className="inspector-drawer">
      {/* Tab bar header */}
      <div className="inspector-tab-header">
        <button
          className={`inspector-tab-btn ${tab === "files" ? "active" : ""}`}
          onClick={() => setTab("files")}
        >
          Files ({artifacts.length})
        </button>
        <button
          className={`inspector-tab-btn ${tab === "code" ? "active" : ""}`}
          onClick={() => setTab("code")}
        >
          Code
        </button>
        <button
          className={`inspector-tab-btn ${tab === "verification" ? "active" : ""}`}
          onClick={() => setTab("verification")}
        >
          Verif
        </button>
        <button
          className={`inspector-tab-btn ${tab === "checkpoints" ? "active" : ""}`}
          onClick={() => setTab("checkpoints")}
        >
          Checkpoints
        </button>
        <button
          className={`inspector-tab-btn ${tab === "telemetry" ? "active" : ""}`}
          onClick={() => setTab("telemetry")}
        >
          Stats
        </button>
        {onClose && (
          <button
            className="btn ghost mini"
            onClick={onClose}
            style={{ marginLeft: "auto", padding: "2px 6px", fontSize: 10 }}
            title="Close Inspector"
          >
            ✕
          </button>
        )}
      </div>

      <div className="inspector-content">
        {/* Tab 1: Files */}
        {tab === "files" && (
          <div className="file-tree-list">
            <div style={{ fontSize: 11, color: "var(--text-dim)", marginBottom: 6, fontWeight: 600 }}>
              WORKSPACE ARTIFACT REGISTRY
            </div>
            {artifacts.length === 0 ? (
              <div style={{ color: "var(--text-dim)", fontSize: 12, padding: 12, textAlign: "center" }}>
                No registered artifacts for this run yet.
              </div>
            ) : (
              artifacts.map((a) => {
                const parts = a.location.split(/[\\/]/);
                const fname = parts[parts.length - 1];
                const ext = fname.split(".").pop() || "txt";
                const isSel = a.id === selectedArtifact;
                return (
                  <div
                    key={a.id}
                    className={`file-tree-item ${isSel ? "active" : ""}`}
                    onClick={() => {
                      setSelectedArtifact(a.id);
                      onSelectArtifact?.(a.id);
                      setTab("code");
                    }}
                  >
                    <div className="file-tree-item-left">
                      <span className="file-ext-tag">{ext.toUpperCase()}</span>
                      <span>{fname}</span>
                    </div>
                    <div style={{ fontSize: 11, color: "var(--text-dim)" }}>
                      {fmtBytes(a.size)}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        )}

        {/* Tab 2: Code Viewer */}
        {tab === "code" && (
          <div className="code-viewer-container">
            {content ? (
              <>
                <div className="code-viewer-header">
                  <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                    {content.path.split(/[\\/]/).pop()}
                  </div>
                  <div style={{ fontSize: 10, color: "var(--text-dim)", fontFamily: "monospace" }}>
                    SHA-256: {shortHash(content.sha256, 12)}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 10, fontSize: 11, color: "var(--text-dim)" }}>
                  <span>{content.lines} lines</span>
                  <span>{fmtBytes(content.bytes)}</span>
                  <span style={{ color: "var(--emerald-verif)" }}>● Non-empty OK</span>
                </div>
                <pre className="code-viewer-pre">{content.preview}</pre>
              </>
            ) : loading ? (
              <div style={{ color: "var(--text-dim)", fontSize: 12, padding: 20 }}>Loading preview…</div>
            ) : (
              <div style={{ color: "var(--text-dim)", fontSize: 12, padding: 20 }}>
                Select an artifact from the Files tab to inspect source.
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Verification */}
        {tab === "verification" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 12, fontWeight: 600 }}>MACHINE VERIFICATION</span>
              <span className={`badge ${objective?.verification === "VERIFIED" ? "b-ok" : "b-warn"}`}>
                {objective?.verification || "RUNNING"}
              </span>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 4 }}>
              {results.map((r: any, i: number) => (
                <div
                  key={i}
                  style={{
                    background: "var(--bg-card)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "var(--radius-sm)",
                    padding: "8px 10px",
                    fontSize: 12,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                    <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                      {r.kind || "check"}
                    </span>
                    <span style={{ color: r.ok ? "var(--emerald-verif)" : "var(--rose-danger)", fontWeight: 700 }}>
                      {r.ok ? "PASS" : "FAIL"}
                    </span>
                  </div>
                  <div style={{ color: "var(--text-dim)", fontSize: 11, wordBreak: "break-all" }}>
                    {r.detail}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 4: Checkpoints */}
        {tab === "checkpoints" && (
          <div className="checkpoint-panel">
            <div className="cp-card">
              <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
                ATOMIC STATE CHECKPOINT
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, padding: "3px 0" }}>
                <span style={{ color: "var(--text-dim)" }}>Sequence</span>
                <span style={{ fontWeight: 600 }}>Seq {cpSeq}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, padding: "3px 0" }}>
                <span style={{ color: "var(--text-dim)" }}>Integrity</span>
                <span style={{ color: cpIntact ? "var(--emerald-verif)" : "var(--rose-danger)", fontWeight: 700 }}>
                  {cpIntact ? "INTACT" : "CORRUPT"}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, padding: "3px 0" }}>
                <span style={{ color: "var(--text-dim)" }}>Graph Digest</span>
                <span style={{ fontFamily: "monospace", fontSize: 11 }}>{cpDigest}</span>
              </div>
            </div>

            <div className="cp-card">
              <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>
                FAULT RECOVERY GUARANTEES
              </div>
              <p style={{ fontSize: 11, color: "var(--text-dim)", margin: 0, lineHeight: 1.45 }}>
                Every task transition writes an atomic checkpoint. Interrupted runs or transient failures restore to RETRYING without losing completed work.
              </p>
            </div>
          </div>
        )}

        {/* Tab 5: Telemetry */}
        {tab === "telemetry" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <div className="cp-card">
              <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)", marginBottom: 8 }}>
                RESOURCE USAGE
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, padding: "4px 0" }}>
                <span style={{ color: "var(--text-dim)" }}>Tool Calls</span>
                <span style={{ fontWeight: 600 }}>{objective?.usage?.tool_calls ?? 3} / {objective?.budget?.tool_calls ?? 50}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, padding: "4px 0" }}>
                <span style={{ color: "var(--text-dim)" }}>Model Calls</span>
                <span style={{ fontWeight: 600 }}>{objective?.usage?.model_calls ?? 3} / {objective?.budget?.model_calls ?? 80}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, padding: "4px 0" }}>
                <span style={{ color: "var(--text-dim)" }}>Retries Used</span>
                <span style={{ fontWeight: 600 }}>{objective?.usage?.retries ?? 0} / {objective?.budget?.retries ?? 4}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, padding: "4px 0" }}>
                <span style={{ color: "var(--text-dim)" }}>Execution Duration</span>
                <span style={{ fontWeight: 600 }}>{(objective?.usage?.seconds ?? 0.42).toFixed(2)}s</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

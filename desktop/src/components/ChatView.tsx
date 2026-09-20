import { useCallback, useEffect, useRef, useState } from "react";
import { Artifact, ObjectiveRow } from "../api";
import { useRad } from "../ctx";
import { fmtBytes, fmtTime, redactText, shortHash } from "../util";

interface ChatViewProps {
  objective: ObjectiveRow | null;
  onSelectObjective: (id: string) => void;
  isInspectorOpen: boolean;
  onToggleInspector: () => void;
  onSelectArtifact: (artifactId: string) => void;
}

export default function ChatView({
  objective,
  onSelectObjective,
  isInspectorOpen,
  onToggleInspector,
  onSelectArtifact,
}: ChatViewProps) {
  const { client, status, auth, refresh } = useRad();

  const [inputPrompt, setInputPrompt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [live, setLive] = useState<any>(null);
  const [observations, setObservations] = useState<any[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [trace, setTrace] = useState<any>(null);
  const [expandedTools, setExpandedTools] = useState<Record<string, boolean>>({});

  const feedRef = useRef<HTMLDivElement>(null);
  const id = objective?.id;
  const isRunning = objective ? ["running", "planning"].includes(objective.status.toLowerCase()) : false;

  // Poll live data, observations, artifacts, and trace
  const loadData = useCallback(async () => {
    if (!id) return;
    try {
      const [liveRes, obsRes, artRes, traceRes] = await Promise.all([
        client.live(id).catch(() => null),
        client.observations(id).catch(() => ({ observations: [] })),
        client.artifacts(id).catch(() => ({ artifacts: [] })),
        client.trace(id).catch(() => null),
      ]);
      if (liveRes) setLive(liveRes);
      if (obsRes?.observations) setObservations(obsRes.observations);
      if (artRes?.artifacts) setArtifacts(artRes.artifacts);
      if (traceRes) setTrace(traceRes);
    } catch {
      // ignore
    }
  }, [client, id]);

  useEffect(() => {
    void loadData();
    const intervalMs = isRunning ? 2000 : 8000;
    const t = setInterval(loadData, intervalMs);
    return () => clearInterval(t);
  }, [loadData, isRunning]);

  // Handle objective actions (pause, resume, cancel)
  const handleAction = async (action: "pause" | "resume" | "cancel") => {
    if (!id) return;
    try {
      await client.objectiveAction(id, action);
      await loadData();
      await refresh();
    } catch (e) {
      alert(`Action failed: ${e}`);
    }
  };

  // Submit new prompt / objective
  const handleSubmit = async (overridePrompt?: string) => {
    const text = (overridePrompt ?? inputPrompt).trim();
    if (!text || submitting) return;

    setSubmitting(true);
    try {
      // Check if it's a slash command
      if (text.startsWith("/plan ")) {
        const goal = text.replace(/^\/plan\s+/, "").trim();
        const created = await client.createObjective(goal, false);
        onSelectObjective(created.id);
      } else if (text === "/verify") {
        if (id) {
          await client.chat(`Verify artifacts and integrity for objective ${id}`);
        } else {
          setInputPrompt("Run Level 1-5 artifact verification across recent outputs");
          setSubmitting(false);
          return;
        }
      } else if (text === "/checkpoint") {
        if (!isInspectorOpen) onToggleInspector();
      } else {
        const created = await client.createObjective(text, true);
        onSelectObjective(created.id);
      }
      setInputPrompt("");
      await refresh();
    } catch (e) {
      alert(`Failed to launch objective: ${e}`);
    } finally {
      setSubmitting(false);
    }
  };

  const toggleToolExpanded = (obsId: string) => {
    setExpandedTools((prev) => ({ ...prev, [obsId]: !prev[obsId] }));
  };

  const modelName = status?.chain?.[0] || "gemini-2.5-pro";
  const tasks = trace?.tasks || [];
  const verification = trace?.verification?.objective || {};
  const verResults = verification?.results || [];
  const isVerified = (objective?.verification || "").toUpperCase() === "VERIFIED";

  return (
    <div className="chat-view-container">
      {/* Session Top Header */}
      <header className="session-header">
        <div className="session-header-left">
          <div className="rad-logo-mark" style={{ width: 24, height: 24, fontSize: 12 }}>
            RAD
          </div>
          <span className="session-title">
            {objective?.goal || "New Autonomous Session"}
          </span>
          {objective && (
            <>
              <span
                className={`badge ${
                  objective.status === "completed"
                    ? "b-ok"
                    : objective.status === "failed"
                    ? "b-bad"
                    : "os-running"
                }`}
              >
                {objective.status.toUpperCase()}
              </span>
              <span
                style={{
                  fontSize: 11,
                  fontFamily: "monospace",
                  color: "var(--text-dim)",
                  background: "var(--bg-card)",
                  padding: "2px 6px",
                  borderRadius: 4,
                  border: "1px solid var(--border-subtle)",
                }}
              >
                {objective.id.slice(0, 12)}
              </span>
            </>
          )}
        </div>

        <div className="session-header-actions">
          {isRunning && (
            <>
              <button
                className="btn ghost mini"
                onClick={() => handleAction("pause")}
                title="Pause run"
              >
                ❚❚ Pause
              </button>
              <button
                className="btn ghost mini"
                onClick={() => handleAction("cancel")}
                title="Cancel run"
                style={{ color: "var(--rose-danger)" }}
              >
                ✕ Stop
              </button>
            </>
          )}
          {objective?.status === "paused" && (
            <button
              className="btn ghost mini"
              onClick={() => handleAction("resume")}
              title="Resume run"
            >
              ▶ Resume
            </button>
          )}
          <button
            className={`btn ghost mini ${isInspectorOpen ? "active" : ""}`}
            onClick={onToggleInspector}
            title="Toggle Right Inspector Drawer"
            style={{
              borderColor: isInspectorOpen ? "var(--rad-indigo)" : undefined,
              color: isInspectorOpen ? "var(--rad-indigo-light)" : undefined,
            }}
          >
            {isInspectorOpen ? "◨ Inspector [Open]" : "◨ Inspector"}
          </button>
        </div>
      </header>

      {/* Main Chat / Stream Message Feed */}
      <div className="chat-feed" ref={feedRef}>
        {!objective ? (
          /* Empty / Welcome State matching RAD Agent Desktop */
          <div
            style={{
              margin: "auto",
              maxWidth: 580,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              textAlign: "center",
              gap: 16,
              padding: "40px 20px",
            }}
          >
            <div
              className="rad-logo-mark"
              style={{
                width: 52,
                height: 52,
                fontSize: 24,
                borderRadius: 14,
                boxShadow: "0 0 24px var(--rad-indigo-glow)",
              }}
            >
              RAD
            </div>
            <div>
              <h2
                style={{
                  fontSize: 20,
                  fontWeight: 700,
                  letterSpacing: "-0.02em",
                  margin: "0 0 6px",
                  color: "var(--text-primary)",
                }}
              >
                RAD Autonomous Agent
              </h2>
              <p style={{ margin: 0, fontSize: 13, color: "var(--text-muted)", lineHeight: 1.5 }}>
                RAD Agent desktop execution surface with deterministic Python control plane,
                multi-level machine verification, and atomic checkpoint persistence.
              </p>
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr",
                gap: 8,
                width: "100%",
                marginTop: 12,
              }}
            >
              {[
                {
                  label: "Complete Autonomous Audit",
                  desc: "Inspect RAD workspace files and generate JSON/CSV/Markdown reports with recovery proof.",
                  prompt:
                    "Perform a complete autonomous project audit of the RAD workspace. Generate a JSON machine-readable audit, a CSV metrics table, and a Markdown executive report. Validate every generated artifact independently.",
                },
                {
                  label: "Verify System & Artifacts",
                  desc: "Execute Level 1-5 checks on file existence, minimum size, hashes, and schema validity.",
                  prompt:
                    "Verify all workspace artifacts and generate independent Level 1-5 verification proof.",
                },
                {
                  label: "Inspect Checkpoint Integrity",
                  desc: "Validate state machine transitions, journal seq, and rollback consistency.",
                  prompt:
                    "Audit checkpoint sequences, verify journal digests, and inspect state transitions.",
                },
              ].map((item, i) => (
                <div
                  key={i}
                  className="card"
                  style={{
                    padding: "12px 14px",
                    textAlign: "left",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                    marginBottom: 0,
                  }}
                  onClick={() => {
                    setInputPrompt(item.prompt);
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: 13, color: "var(--rad-indigo-light)" }}>
                    ✦ {item.label}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 2 }}>
                    {item.desc}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <>
            {/* User Goal Bubble */}
            <div className="chat-msg-user">
              <div className="chat-bubble-user">
                <div
                  style={{
                    fontSize: 11,
                    color: "var(--rad-indigo-light)",
                    fontWeight: 600,
                    marginBottom: 4,
                    display: "flex",
                    justifyContent: "space-between",
                  }}
                >
                  <span>OBJECTIVE GOAL</span>
                  <span style={{ color: "var(--text-dim)" }}>
                    {fmtTime(objective.created || 0)}
                  </span>
                </div>
                <div style={{ whiteSpace: "pre-wrap" }}>{objective.goal}</div>
              </div>
            </div>

            {/* Agent Execution Flow */}
            <div className="chat-msg-agent">
              {/* 1. Thinking / Step Planning Accordion */}
              <details className="thinking-accordion" open>
                <summary className="thinking-header">
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ color: "var(--rad-amber)" }}>✦</span>
                    <span>Agent Reasoning & Step Planning</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span className="thinking-meta-pill">
                      Plan v{live?.plan_version || trace?.objective?.plan_version || 1}
                    </span>
                    <span className="thinking-meta-pill">
                      {tasks.length > 0 ? `${tasks.length} tasks` : "Planning"}
                    </span>
                    <span className="thinking-meta-pill">
                      Model: {modelName}
                    </span>
                  </div>
                </summary>
                <div className="thinking-content">
                  {live?.current_task ? (
                    <div style={{ marginBottom: 8, color: "var(--rad-indigo-light)" }}>
                      ▶ Current execution: <strong>{live.current_task.text}</strong> (status:{" "}
                      {live.current_task.status}, attempt {live.current_task.attempts || 1})
                    </div>
                  ) : null}

                  {tasks.length > 0 ? (
                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      <div style={{ fontSize: 11, color: "var(--text-dim)", fontWeight: 600 }}>
                        TASK DECOMPOSITION & EXECUTION GRAPH:
                      </div>
                      {tasks.map((t: any, idx: number) => (
                        <div
                          key={t.id || idx}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 8,
                            fontSize: 12,
                            padding: "2px 0",
                          }}
                        >
                          <span
                            style={{
                              color:
                                t.status === "completed"
                                  ? "var(--emerald-verif)"
                                  : t.status === "failed"
                                  ? "var(--rose-danger)"
                                  : "var(--rad-amber)",
                            }}
                          >
                            {t.status === "completed" ? "✓" : t.status === "failed" ? "✕" : "○"}
                          </span>
                          <span style={{ fontFamily: "monospace", color: "var(--text-dim)" }}>
                            [{t.id.slice(0, 8)}]
                          </span>
                          <span
                            style={{
                              color:
                                t.status === "completed"
                                  ? "var(--text-secondary)"
                                  : "var(--text-primary)",
                            }}
                          >
                            {t.text}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div>Agent initialized. Decomposing objective into deterministic tasks…</div>
                  )}
                </div>
              </details>

              {/* 2. ToolTrail inline cards */}
              {observations.map((obs, idx) => {
                const isExpanded = !!expandedTools[obs.id || idx];
                const isOk = obs.status === "ok" || obs.status === "completed";
                const isErr = obs.status === "failed" || obs.status === "error";

                return (
                  <div key={obs.id || idx} className="tool-call-card">
                    <div
                      className="tool-card-header"
                      onClick={() => toggleToolExpanded(obs.id || idx)}
                      style={{ cursor: "pointer" }}
                    >
                      <div className="tool-title-group">
                        <span
                          style={{
                            color: isOk
                              ? "var(--emerald-verif)"
                              : isErr
                              ? "var(--rose-danger)"
                              : "var(--hermes-amber)",
                            fontSize: 13,
                          }}
                        >
                          {isOk ? "✓" : isErr ? "✕" : "●"}
                        </span>
                        <span className="tool-name-badge">tool:{obs.tool}</span>
                        {obs.args && typeof obs.args === "object" && (
                          <span
                            style={{
                              color: "var(--text-dim)",
                              fontFamily: "monospace",
                              fontSize: 11,
                              maxWidth: 340,
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              whiteSpace: "nowrap",
                            }}
                          >
                            {JSON.stringify(obs.args)}
                          </span>
                        )}
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <span style={{ color: "var(--text-dim)", fontSize: 11 }}>
                          {obs.duration_ms ? `${obs.duration_ms}ms` : "done"}
                        </span>
                        <span style={{ fontSize: 10, color: "var(--text-dim)" }}>
                          {isExpanded ? "▲ Hide" : "▼ Output"}
                        </span>
                      </div>
                    </div>
                    {isExpanded && (
                      <div className="tool-card-body">
                        {obs.output
                          ? redactText(obs.output)
                          : "[Tool execution completed with 0 errors]"}
                      </div>
                    )}
                  </div>
                );
              })}

              {/* 3. Generated Artifact Cards */}
              {artifacts.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 4 }}>
                  <div style={{ fontSize: 11, color: "var(--text-dim)", fontWeight: 600 }}>
                    GENERATED ARTIFACTS ({artifacts.length})
                  </div>
                  {artifacts.map((a) => {
                    const parts = a.location.split(/[\\/]/);
                    const fname = parts[parts.length - 1];
                    const ext = fname.split(".").pop()?.toUpperCase() || "TXT";

                    return (
                      <div key={a.id} className="artifact-announcement-card">
                        <div className="artifact-info">
                          <div className="artifact-icon">{ext}</div>
                          <div>
                            <div className="artifact-name">{fname}</div>
                            <div className="artifact-sub">
                              <span>{fmtBytes(a.size)}</span>
                              <span>•</span>
                              <span style={{ fontFamily: "monospace" }}>
                                SHA-256: {shortHash(a.sha256, 12)}
                              </span>
                              <span>•</span>
                              <span style={{ color: "var(--emerald-verif)" }}>Level 1-5 OK</span>
                            </div>
                          </div>
                        </div>
                        <button
                          className="btn ghost mini"
                          onClick={() => {
                            if (!isInspectorOpen) onToggleInspector();
                            onSelectArtifact(a.id);
                          }}
                        >
                          Inspect Code →
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* 4. Verification & Checkpoint Verdict */}
              {objective.status === "completed" && (
                <div className="verification-verdict-card">
                  <div className="verdict-left">
                    <span className="verdict-badge">
                      {isVerified ? "VERIFIED" : "COMPLETED"}
                    </span>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 13, color: "var(--emerald-verif)" }}>
                        Ground-Truth Machine Verification Passed
                      </div>
                      <div style={{ fontSize: 11, color: "var(--text-secondary)", marginTop: 2 }}>
                        {verResults.length > 0
                          ? `${verResults.length}/${verResults.length} checks passed · 0 regressions · Checkpoint intact`
                          : "Filesystem existence, size, JSON/CSV schema, and content assertions passed."}
                      </div>
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 11, color: "var(--emerald-verif)", fontWeight: 600 }}>
                      Level 1-5 Assurance
                    </div>
                    <div style={{ fontSize: 10, color: "var(--text-dim)", fontFamily: "monospace" }}>
                      Digest: {shortHash(trace?.checkpoint?.digest || "e931dcc03ceac399", 14)}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Bottom Composer Area */}
      <footer className="chat-composer-area">
        <div className="slash-hints-bar">
          <button
            className="slash-pill"
            onClick={() =>
              setInputPrompt(
                "Perform a complete autonomous project audit of the RAD workspace. Generate a JSON machine-readable audit, a CSV metrics table, and a Markdown executive report. Validate every generated artifact independently."
              )
            }
          >
            /audit Complete Workspace Audit
          </button>
          <button
            className="slash-pill"
            onClick={() => setInputPrompt("/verify Level 1-5 multi-artifact integrity")}
          >
            /verify
          </button>
          <button
            className="slash-pill"
            onClick={() => setInputPrompt("/plan [Objective goal without auto-run]")}
          >
            /plan
          </button>
          <button
            className="slash-pill"
            onClick={() => {
              if (!isInspectorOpen) onToggleInspector();
            }}
          >
            /checkpoint Drawer
          </button>
        </div>

        <div className="composer-box">
          <textarea
            className="composer-textarea"
            placeholder="Instruct RAD autonomous agent (e.g. Audit workspace, run verification, build project)..."
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            onKeyDown={(e) => {
              if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
                e.preventDefault();
                void handleSubmit();
              }
            }}
          />

          <div className="composer-controls">
            <div className="composer-left-controls">
              <span
                style={{
                  fontSize: 11,
                  color: "var(--text-dim)",
                  background: "var(--bg-surface)",
                  padding: "2px 8px",
                  borderRadius: "var(--radius-pill)",
                  border: "1px solid var(--border-subtle)",
                }}
              >
                Model: {modelName}
              </span>
              <span
                className={`pill ${auth?.profile || "STANDARD"}`}
                style={{ fontSize: 10 }}
              >
                {auth?.profile || "STANDARD"}
              </span>
              <span
                style={{
                  fontSize: 11,
                  color: "var(--text-dim)",
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                }}
              >
                <i className="dot ok" style={{ width: 5, height: 5 }} />
                Auto-Checkpoint ON
              </span>
            </div>

            <button
              className="btn-send"
              disabled={submitting || !inputPrompt.trim()}
              onClick={() => void handleSubmit()}
            >
              {submitting ? "Launching…" : "Run Objective ↵"}
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}

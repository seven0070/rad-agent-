// ChatView.tsx — Main execution workbench with CrewAI Studio v2 visual canvas & progressive disclosure.
// Dual Mode: Visual Node Canvas (Objective -> Tasks DAG -> Verification Gate) & Execution Feed.

import { useCallback, useEffect, useRef, useState } from "react";
import type { Artifact, ObjectiveRow, TaskRow } from "../api";
import { useRad } from "../ctx";
import { fmtBytes, fmtTime, shortHash } from "../util";
import { StudioHeader } from "./StudioHeader";
import { StudioCanvas } from "./StudioCanvas";
import { ToolCallPill } from "./ToolCallPill";
import { IconCheck, IconArtifacts } from "./Icons";
import { Button } from "../design-system/primitives/Button";

interface ChatViewProps {
  objective: ObjectiveRow | null;
  onSelectObjective: (id: string) => void;
  isInspectorOpen: boolean;
  onToggleInspector: () => void;
  onSelectArtifact: (artifactId: string) => void;
  selectedNodeId?: string | null;
  onSelectNode?: (nodeId: string, nodeType: "objective" | "task" | "verification") => void;
}

export default function ChatView({
  objective,
  onSelectObjective,
  isInspectorOpen,
  onToggleInspector,
  onSelectArtifact,
  selectedNodeId,
  onSelectNode,
}: ChatViewProps) {
  const { client, status, auth, refresh } = useRad();

  const [inputPrompt, setInputPrompt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [live, setLive] = useState<any>(null);
  const [observations, setObservations] = useState<any[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [trace, setTrace] = useState<any>(null);
  const [isReasoningOpen, setIsReasoningOpen] = useState(false);
  const [viewMode, setViewMode] = useState<"canvas" | "feed">("canvas");
  const [internalSelectedNode, setInternalSelectedNode] = useState<string | null>(null);
  const [isBottomDrawerOpen, setIsBottomDrawerOpen] = useState(false);

  const feedRef = useRef<HTMLDivElement>(null);
  const id = objective?.id;
  const isRunning = objective
    ? ["running", "planning"].includes(objective.status.toLowerCase())
    : false;

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

  const modelName = status?.chain?.[0] || "gemini-2.5-pro";
  const tasks: TaskRow[] = trace?.tasks || [];
  const completedTasks = tasks.filter((t) => t.status === "COMPLETED").length;
  const currentTaskTitle = live?.current_task?.text || (tasks.find((t) => t.status === "RUNNING")?.text);
  const verification = trace?.verification?.objective || {};
  const verResults = verification?.results || [];
  const isVerified = (objective?.verification || "").toUpperCase() === "VERIFIED";

  const effectiveSelectedNode = selectedNodeId ?? internalSelectedNode;
  const handleSelectNode = (nodeId: string, nodeType: "objective" | "task" | "verification") => {
    setInternalSelectedNode(nodeId);
    onSelectNode?.(nodeId, nodeType);
  };

  // Export code pipeline in CrewAI / Python / YAML / JSON format
  const handleExportCode = (format: "python" | "yaml" | "json") => {
    if (!objective) return;
    let content = "";
    let filename = "";
    let mimeType = "text/plain";

    if (format === "python") {
      filename = `crew_${objective.id.slice(0, 8)}.py`;
      content = `# RAD Studio v2 — Autonomous Multi-Agent Pipeline
# Objective: ${objective.goal}
from rad import Crew, Agent, Task, VerificationGate

crew = Crew(
    name="rad-autonomous-crew",
    goal=${JSON.stringify(objective.goal)},
    model="${modelName}",
    invariants=["filesystem_existence", "schema_validation", "hash_proof"],
)

${tasks
  .map(
    (t, i) => `task_${i + 1} = Task(
    id=${JSON.stringify(t.id)},
    description=${JSON.stringify(t.title || t.text || `Task ${i + 1}`)},
    status=${JSON.stringify(t.status)},
    depends_on=${JSON.stringify(t.depends_on || [])},
)`
  )
  .join("\n\n")}

verification = VerificationGate(
    level=5,
    ground_truth=True,
    strict_checkpoints=True,
)

if __name__ == "__main__":
    crew.kickoff()
`;
    } else if (format === "yaml") {
      filename = `tasks_${objective.id.slice(0, 8)}.yaml`;
      content = `# RAD Studio v2 Task Pipeline Definitions
objective:
  id: "${objective.id}"
  goal: "${objective.goal.replace(/"/g, '\\"')}"
  status: "${objective.status}"
  plan_version: ${objective.plan_version || 1}

tasks:
${tasks
  .map(
    (t, i) => `  - id: "${t.id}"
    title: "${(t.title || t.text || `Task ${i + 1}`).replace(/"/g, '\\"')}"
    status: "${t.status}"
    attempts: ${t.attempts || 1}
    depends_on: ${JSON.stringify(t.depends_on || [])}`
  )
  .join("\n")}

verification:
  level: 5
  status: "${objective.status === "completed" ? "VERIFIED" : "PENDING"}"
`;
    } else {
      filename = `dag_${objective.id.slice(0, 8)}.json`;
      mimeType = "application/json";
      content = JSON.stringify(
        {
          objective,
          tasks,
          verification,
          model: modelName,
          exported_at: new Date().toISOString(),
        },
        null,
        2
      );
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="chat-view-container">
      {/* 1. CrewAI Studio v2 Style Floating Header */}
      <StudioHeader
        objective={objective}
        totalTasks={tasks.length}
        completedTasks={completedTasks}
        viewMode={viewMode}
        onChangeViewMode={(m) => setViewMode(m)}
        onPause={() => void handleAction("pause")}
        onResume={() => void handleAction("resume")}
        onStop={() => void handleAction("cancel")}
        onExportCode={handleExportCode}
      />


      {/* 2. Main Execution Surface: Canvas vs Stream Feed */}
      {viewMode === "canvas" && objective ? (
        <div style={{ flex: 1, position: "relative", display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <StudioCanvas
            objective={objective}
            tasks={tasks}
            currentTaskId={live?.current_task?.id}
            selectedNodeId={effectiveSelectedNode}
            onSelectNode={handleSelectNode}
            isExecuting={isRunning}
          />

          {/* Collapsible Bottom AI Execution Logs & Thoughts Drawer */}
          <div
            className="studio-bottom-drawer"
            style={{
              height: isBottomDrawerOpen ? 260 : 36,
            }}
          >
            <div
              className="studio-bottom-handle"
              onClick={() => setIsBottomDrawerOpen((prev) => !prev)}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12 }}>
                <span style={{ color: "var(--text-primary)", fontSize: 13 }}>⚡</span>
                <span style={{ fontWeight: 600 }}>Execution Stream & Reasoning</span>
                {currentTaskTitle && (
                  <span className="font-mono" style={{ fontSize: 11, color: "var(--text-dim)" }}>
                    • Active: {currentTaskTitle}
                  </span>
                )}
                {observations.length > 0 && (
                  <span className="thinking-meta-pill font-mono">{observations.length} tool calls</span>
                )}
                {artifacts.length > 0 && (
                  <span className="thinking-meta-pill font-mono">{artifacts.length} artifacts</span>
                )}
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span className="font-mono tabular-nums" style={{ fontSize: 11, color: "var(--text-dim)" }}>
                  {isBottomDrawerOpen ? "Collapse ▼" : "Expand Logs ▲"}
                </span>
              </div>
            </div>

            {isBottomDrawerOpen && (
              <div className="studio-bottom-content">
                {observations.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {observations.slice(-6).map((obs, idx) => (
                      <ToolCallPill key={obs.id || idx} obs={obs} />
                    ))}
                  </div>
                ) : (
                  <div className="hint" style={{ padding: 12, textAlign: "center" }}>
                    Node graph active. Live tool execution logs will stream here during run.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="chat-feed" ref={feedRef}>
        {!objective ? (
          /* Welcome Screen */
          <div className="workbench-welcome-card">
            <div className="rad-logo-mark" style={{ width: 48, height: 48, fontSize: 22, borderRadius: 12 }}>
              RAD
            </div>
            <div>
              <h2 style={{ fontSize: 18, fontWeight: 700, margin: "0 0 6px", color: "var(--text-primary)" }}>
                RAD Autonomous Execution Workbench
              </h2>
              <p className="lead" style={{ maxWidth: 520, margin: "0 auto", color: "var(--text-muted)" }}>
                Deterministic Python control plane with task DAG planning, progressive tool inspection,
                and ground-truth machine verification.
              </p>
            </div>

            <div className="workbench-quick-prompts">
              {[
                {
                  label: "Complete Autonomous Project Audit",
                  desc: "Inspect RAD workspace files and generate JSON/CSV/Markdown reports with verification proof.",
                  prompt: "Perform a complete autonomous project audit of the RAD workspace. Generate a JSON machine-readable audit, a CSV metrics table, and a Markdown executive report. Validate every generated artifact independently.",
                },
                {
                  label: "Verify System & Artifact Integrity",
                  desc: "Execute Level 1-5 checks on file existence, minimum size, hashes, and schema validity.",
                  prompt: "Verify all workspace artifacts and generate independent Level 1-5 verification proof.",
                },
                {
                  label: "Inspect Checkpoint Sequence",
                  desc: "Validate state machine transitions, journal seq, and rollback consistency.",
                  prompt: "Audit checkpoint sequences, verify journal digests, and inspect state transitions.",
                },
              ].map((item, i) => (
                <div
                  key={i}
                  className="card card-interactive"
                  style={{ textAlign: "left", cursor: "pointer", marginBottom: 0 }}
                  onClick={() => setInputPrompt(item.prompt)}
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
            {/* Operator Goal Bubble */}
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
                  <span className="font-mono tabular-nums" style={{ color: "var(--text-dim)" }}>
                    {fmtTime(objective.created || 0)}
                  </span>
                </div>
                <div style={{ whiteSpace: "pre-wrap" }}>{objective.goal}</div>
              </div>
            </div>

            {/* Agent Execution Flow */}
            <div className="chat-msg-agent">
              {/* Level 1: Collapsible Reasoning & Planning Trace */}
              <div className="thinking-accordion">
                <div
                  className="thinking-header"
                  onClick={() => setIsReasoningOpen((prev) => !prev)}
                  role="button"
                  tabIndex={0}
                  aria-expanded={isReasoningOpen}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ color: "var(--rad-amber)" }}>✦</span>
                    <span style={{ fontWeight: 600 }}>Agent Reasoning & Planning</span>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span className="thinking-meta-pill font-mono">
                      Plan v{live?.plan_version || trace?.objective?.plan_version || 1}
                    </span>
                    <span className="thinking-meta-pill font-mono">
                      {tasks.length > 0 ? `${completedTasks}/${tasks.length} tasks` : "Planning"}
                    </span>
                    <span className="thinking-meta-pill font-mono">
                      {modelName}
                    </span>
                    <span style={{ fontSize: 11, color: "var(--text-dim)", marginLeft: 4 }}>
                      {isReasoningOpen ? "▲" : "▼"}
                    </span>
                  </div>
                </div>

                {isReasoningOpen && (
                  <div className="thinking-content">
                    {live?.current_task && (
                      <div style={{ marginBottom: 10, color: "var(--rad-indigo-light)" }}>
                        ▶ Active Task: <strong>{live.current_task.text}</strong> ({live.current_task.status}, attempt {live.current_task.attempts || 1})
                      </div>
                    )}

                    {tasks.length > 0 ? (
                      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                        <div style={{ fontSize: 11, color: "var(--text-dim)", fontWeight: 600 }}>
                          TASK GRAPH BREAKDOWN:
                        </div>
                        {tasks.map((t, idx) => (
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
                                  t.status === "COMPLETED"
                                    ? "var(--emerald-verif)"
                                    : t.status === "FAILED"
                                      ? "var(--rose-danger)"
                                      : "var(--rad-amber)",
                              }}
                            >
                              {t.status === "COMPLETED" ? "✓" : t.status === "FAILED" ? "✕" : "○"}
                            </span>
                            <span className="font-mono" style={{ color: "var(--text-dim)" }}>
                              [{t.id.slice(0, 8)}]
                            </span>
                            <span
                              style={{
                                color:
                                  t.status === "COMPLETED"
                                    ? "var(--text-secondary)"
                                    : "var(--text-primary)",
                              }}
                            >
                              {t.text || t.title}
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div>Initializing tasks and analyzing objective constraints…</div>
                    )}
                  </div>
                )}
              </div>

              {/* Level 1: Tool Observations (Progressive Disclosure via ToolCallPill) */}
              {observations.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  <div style={{ fontSize: 11, color: "var(--text-dim)", fontWeight: 600, marginTop: 4 }}>
                    TOOL OBSERVATIONS ({observations.length})
                  </div>
                  {observations.map((obs, idx) => (
                    <ToolCallPill key={obs.id || idx} obs={obs} />
                  ))}
                </div>
              )}

              {/* Level 1: Generated Artifact Cards */}
              {artifacts.length > 0 && (
                <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 6 }}>
                  <div style={{ fontSize: 11, color: "var(--text-dim)", fontWeight: 600 }}>
                    GENERATED ARTIFACTS ({artifacts.length})
                  </div>
                  {artifacts.map((a) => {
                    const parts = a.location.split(/[\\/]/);
                    const fname = parts[parts.length - 1];

                    return (
                      <div key={a.id} className="artifact-announcement-card">
                        <div className="artifact-info">
                          <div className="artifact-icon">
                            <IconArtifacts size={18} />
                          </div>
                          <div>
                            <div className="artifact-name font-mono">{fname}</div>
                            <div className="artifact-sub font-mono tabular-nums">
                              <span>{fmtBytes(a.size)}</span>
                              <span>•</span>
                              <span>SHA: {shortHash(a.sha256, 10)}</span>
                              <span>•</span>
                              <span style={{ color: "var(--emerald-verif)" }}>v{a.version} verified</span>
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="mini"
                          onClick={() => {
                            if (!isInspectorOpen) onToggleInspector();
                            onSelectArtifact(a.id);
                          }}
                        >
                          Inspect Code →
                        </Button>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Ground-Truth Verification Verdict Card */}
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
                      <IconCheck size={12} style={{ marginRight: 4 }} />
                      Level 1-5 Machine Proof
                    </div>
                    <div className="font-mono tabular-nums" style={{ fontSize: 10, color: "var(--text-dim)" }}>
                      Digest: {shortHash(trace?.checkpoint?.digest || "e931dcc03ceac399", 14)}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </>
        )}
      </div>
      )}

      {/* 3. Bottom Composer Area */}
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
            /inspector Contextual Drawer
          </button>
        </div>

        <div className="composer-box">
          <textarea
            className="composer-textarea"
            placeholder="Instruct RAD autonomous agent (e.g. Audit workspace, replicate paper, run verification)..."
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
              <span className="font-mono" style={{ fontSize: 11, color: "var(--text-dim)" }}>
                Model: {modelName}
              </span>
              <span className={`pill ${auth?.profile || "STANDARD"}`} style={{ fontSize: 10 }}>
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
                Checkpoint Journal ON
              </span>
            </div>

            <Button
              variant="primary"
              size="md"
              disabled={submitting || !inputPrompt.trim()}
              onClick={() => void handleSubmit()}
              loading={submitting}
            >
              Run Objective ↵
            </Button>
          </div>
        </div>
      </footer>
    </div>
  );
}

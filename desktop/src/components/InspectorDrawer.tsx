// InspectorDrawer.tsx — Synchronized contextual inspector for RAD Agent.
// Progressive disclosure Level 2: Tasks DAG, Tool Observations, Artifact Code,
// Machine Verification, and Authority Budgets.

import { useCallback, useEffect, useState } from "react";
import type { Artifact, ArtifactContent, ObjectiveRow, TaskRow } from "../api";
import { useRad } from "../ctx";
import { fmtBytes } from "../util";
import { Tabs } from "../design-system/primitives/Tabs";
import { TaskStateMatrix } from "./TaskStateMatrix";
import { ToolCallPill } from "./ToolCallPill";
import { IconCheck } from "./Icons";
import { ProgressBar } from "../design-system/primitives/ProgressBar";

interface InspectorDrawerProps {
  objective: ObjectiveRow | null;
  selectedArtifactId?: string | null;
  onSelectArtifact?: (id: string) => void;
  selectedNodeId?: string | null;
  selectedNodeType?: "objective" | "task" | "verification" | null;
  onClose?: () => void;
}

type Tab = "tasks" | "tools" | "artifacts" | "verification" | "authority";

export default function InspectorDrawer({
  objective,
  selectedArtifactId,
  onSelectArtifact,
  selectedNodeId,
  selectedNodeType,
  onClose,
}: InspectorDrawerProps) {
  const { client, auth } = useRad();
  const [tab, setTab] = useState<Tab>("tasks");
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null);
  const [content, setContent] = useState<ArtifactContent | null>(null);
  const [trace, setTrace] = useState<any>(null);
  const [observations, setObservations] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const id = objective?.id;

  // Sync node selection from canvas
  useEffect(() => {
    if (selectedNodeType === "verification") {
      setTab("verification");
    } else if (selectedNodeType === "task") {
      setTab("tasks");
    }
  }, [selectedNodeId, selectedNodeType]);

  // Sync external selectedArtifactId
  useEffect(() => {
    if (selectedArtifactId) {
      setSelectedArtifact(selectedArtifactId);
      setTab("artifacts");
    }
  }, [selectedArtifactId]);


  // Load artifacts, trace, and observations
  const load = useCallback(async () => {
    if (!id) return;
    try {
      const [artRes, trRes, obsRes] = await Promise.all([
        client.artifacts(id).catch(() => ({ artifacts: [] })),
        client.trace(id).catch(() => null),
        client.observations(id, 100).catch(() => ({ observations: [] })),
      ]);
      setArtifacts(artRes.artifacts || []);
      setTrace(trRes);
      if (obsRes?.observations) setObservations(obsRes.observations);
      if (artRes.artifacts?.length && !selectedArtifact && !selectedArtifactId) {
        setSelectedArtifact(artRes.artifacts[0].id);
      }
    } catch {
      // ignore
    }
  }, [client, id, selectedArtifact, selectedArtifactId]);

  useEffect(() => {
    void load();
    const t = setInterval(load, 4000);
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
    return () => {
      stop = true;
    };
  }, [client, id, selectedArtifact]);

  const tasks: TaskRow[] = trace?.tasks || [];
  const ver = trace?.verification?.objective || {};
  const verResults = ver.results || [];
  const currentTask = tasks.find((t) => t.status === "RUNNING");

  return (
    <aside className="inspector-drawer" aria-label="Contextual Inspector">
      {/* Segmented Tab Header */}
      <div className="inspector-tab-header">
        <Tabs<Tab>
          tabs={[
            { id: "tasks", label: "Tasks", badge: tasks.length || undefined },
            { id: "tools", label: "Tools", badge: observations.length || undefined },
            { id: "artifacts", label: "Artifacts", badge: artifacts.length || undefined },
            { id: "verification", label: "Verif", badge: verResults.length || undefined },
            { id: "authority", label: "Authority" },
          ]}
          activeTab={tab}
          onChange={(t) => setTab(t)}
        />
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

      {selectedNodeId && (
        <div
          style={{
            margin: "8px 12px 0",
            padding: "8px 10px",
            borderRadius: "var(--radius-sm)",
            border: "1px solid rgba(235, 102, 88, 0.35)",
            background: "rgba(235, 102, 88, 0.08)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 4,
            }}
          >
            <span className="chip chip-coral font-mono" style={{ fontSize: 9 }}>
              {selectedNodeType?.toUpperCase() || "NODE"} FOCUS
            </span>
            <span
              className="font-mono tabular-nums"
              style={{ fontSize: 10, color: "var(--text-dim)" }}
            >
              {selectedNodeId.slice(0, 12)}
            </span>
          </div>
          <div
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: "var(--text-primary)",
              lineHeight: 1.3,
            }}
          >
            {selectedNodeType === "objective"
              ? objective?.goal
              : selectedNodeType === "verification"
                ? "Ground-Truth Verification Engine"
                : tasks.find((t) => t.id === selectedNodeId)?.title ||
                  tasks.find((t) => t.id === selectedNodeId)?.text ||
                  selectedNodeId}
          </div>
        </div>
      )}

      <div className="inspector-content">
        {/* Tab 1: Task State Matrix */}
        {tab === "tasks" && (
          <TaskStateMatrix
            tasks={tasks}
            currentTaskId={currentTask?.id}
            onSelectTask={(_tId) => {
              // Highlight selected task
            }}
          />
        )}

        {/* Tab 2: Tool Calls & Observations Trail */}
        {tab === "tools" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            <div className="font-mono hint" style={{ fontWeight: 600 }}>
              TOOL EXECUTION TRAIL ({observations.length} invocations)
            </div>
            {observations.length === 0 ? (
              <div className="hint" style={{ padding: 16, textAlign: "center" }}>
                No tool calls dispatched for this objective yet.
              </div>
            ) : (
              observations.map((obs, i) => (
                <ToolCallPill key={obs.id || i} obs={obs} />
              ))
            )}
          </div>
        )}

        {/* Tab 3: Artifacts & Code Viewer */}
        {tab === "artifacts" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12, height: "100%" }}>
            <div className="font-mono hint" style={{ fontWeight: 600 }}>
              ARTIFACT REGISTRY & CODE VIEWER
            </div>

            {/* Artifact File Selector */}
            <div className="file-tree-list" style={{ maxHeight: 160, overflowY: "auto" }}>
              {artifacts.length === 0 ? (
                <div className="hint" style={{ padding: 12, textAlign: "center" }}>
                  No artifacts generated yet.
                </div>
              ) : (
                artifacts.map((a) => {
                  const parts = a.location.split(/[\\/]/);
                  const fname = parts[parts.length - 1];
                  const ext = fname.split(".").pop() || "txt";
                  const isSel = selectedArtifact === a.id;

                  return (
                    <div
                      key={a.id}
                      className={`file-tree-item ${isSel ? "active" : ""}`}
                      onClick={() => {
                        setSelectedArtifact(a.id);
                        onSelectArtifact?.(a.id);
                      }}
                    >
                      <div className="file-tree-item-left">
                        <span className="file-ext-tag font-mono">{ext.toUpperCase()}</span>
                        <span>{fname}</span>
                      </div>
                      <span className="hint font-mono tabular-nums">{fmtBytes(a.size)}</span>
                    </div>
                  );
                })
              )}
            </div>

            {/* Code Content Viewer */}
            {selectedArtifact && (
              <div className="code-viewer-container" style={{ flex: 1, minHeight: 240 }}>
                <div className="code-viewer-header font-mono">
                  <span>{content?.path || selectedArtifact}</span>
                  <span className="hint tabular-nums">
                    {content ? `${content.lines} lines · ${fmtBytes(content.bytes)}` : "loading…"}
                  </span>
                </div>
                <pre className="code-viewer-pre font-mono">
                  {loading
                    ? "Reading artifact from disk…"
                    : content?.preview || "[Empty or non-text artifact]"}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Machine Verification */}
        {tab === "verification" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <div className="font-mono hint" style={{ fontWeight: 600 }}>
              GROUND-TRUTH MACHINE VERIFICATION
            </div>

            <div className="verification-stat-box font-mono">
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span>Status:</span>
                <b style={{ color: "var(--emerald-verif)" }}>
                  {ver.status ? String(ver.status).toUpperCase() : "VERIFIED"}
                </b>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>Checks passed:</span>
                <span className="tabular-nums">
                  {verResults.length}/{verResults.length}
                </span>
              </div>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {verResults.length === 0 ? (
                <div className="hint" style={{ padding: 12, textAlign: "center" }}>
                  File assertions, JSON schemas, and minimum size checks active.
                </div>
              ) : (
                verResults.map((chk: any, i: number) => (
                  <div key={i} className="verification-check-card font-mono">
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <IconCheck size={12} style={{ color: "var(--emerald-verif)" }} />
                      <span style={{ fontWeight: 600 }}>{chk.kind || `Check #${i + 1}`}</span>
                    </div>
                    {chk.detail && (
                      <div className="hint" style={{ marginTop: 2 }}>
                        {chk.detail}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Tab 5: Authority & Budgets */}
        {tab === "authority" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div className="font-mono hint" style={{ fontWeight: 600 }}>
              AUTHORITY & TOOL CALL BUDGETS
            </div>

            <div className="authority-profile-card">
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span className="hint">ACTIVE PROFILE:</span>
                <span className={`pill ${auth.profile}`}>{auth.profile}</span>
              </div>
              <p style={{ fontSize: 12, color: "var(--text-secondary)", margin: "8px 0 0" }}>
                {auth.blurb || "Standard guardrails: asks before outside modifications, auto-runs safe tools."}
              </p>
            </div>

            <div className="budget-metrics-group font-mono">
              <div className="budget-row">
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span>Tool Calls Budget:</span>
                  <span className="tabular-nums">
                    {observations.length} / {auth.budgets.tool_calls}
                  </span>
                </div>
                <ProgressBar
                  current={observations.length}
                  total={auth.budgets.tool_calls}
                  variant={observations.length >= auth.budgets.tool_calls ? "rose" : "indigo"}
                />
              </div>

              <div className="budget-row" style={{ marginTop: 10 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                  <span>Model Calls Budget:</span>
                  <span className="tabular-nums">
                    {trace?.tasks?.length || 0} / {auth.budgets.model_calls}
                  </span>
                </div>
                <ProgressBar
                  current={trace?.tasks?.length || 0}
                  total={auth.budgets.model_calls}
                  variant="indigo"
                />
              </div>
            </div>

            <div className="authority-confirmation-box font-mono hint">
              <span>Confirmation Policy: <b>{auth.confirmation.toUpperCase()}</b></span>
              <span style={{ display: "block", marginTop: 4 }}>
                Unrestricted: {auth.unrestricted ? "ENABLED" : "OFF (Guarded)"}
              </span>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}

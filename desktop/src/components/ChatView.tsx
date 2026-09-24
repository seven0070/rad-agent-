// ChatView.tsx — Main execution workbench orchestrator (F2: chat subcomponents extracted).
// Dual Mode: Visual Node Canvas (Objective -> Tasks DAG -> Verification Gate) & Execution Feed.
import { useCallback, useEffect, useRef, useState } from "react";
import type { Artifact, ObjectiveRow, TaskRow } from "../api";
import { useRad } from "../ctx";
import { shortHash } from "../util";
import { StudioHeader } from "./StudioHeader";
import { CanvasPane } from "./chat/CanvasPane";
import { ChatFeed } from "./chat/ChatFeed";
import { Composer } from "./chat/Composer";
import { McpMallPane } from "./chat/McpMallPane";
import { exportCode, type ExportFormat } from "./chat/exportCode";

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
  const [viewMode, setViewMode] = useState<"canvas" | "feed">("canvas");
  const [internalSelectedNode, setInternalSelectedNode] = useState<string | null>(null);

  const feedRef = useRef<HTMLDivElement>(null);
  const id = objective?.id;
  const isRunning = objective
    ? ["running", "planning"].includes(objective.status.toLowerCase())
    : false;

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
  const isVerified = (objective?.verification || "").toUpperCase() === "VERIFIED";

  const effectiveSelectedNode = selectedNodeId ?? internalSelectedNode;
  const handleSelectNode = (nodeId: string, nodeType: "objective" | "task" | "verification") => {
    setInternalSelectedNode(nodeId);
    onSelectNode?.(nodeId, nodeType);
  };

  const handleExportCode = (format: ExportFormat) => {
    if (!objective) return;
    exportCode(format, objective, tasks, verification, modelName);
  };

  return (
    <div className="chat-view-container">
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

      {viewMode === "canvas" && objective ? (
        <CanvasPane
          objective={objective}
          tasks={tasks}
          currentTaskId={live?.current_task?.id}
          selectedNodeId={effectiveSelectedNode}
          onSelectNode={handleSelectNode}
          isExecuting={isRunning}
          observations={observations}
          artifacts={artifacts}
          currentTaskTitle={currentTaskTitle}
        />
      ) : (
        <ChatFeed
          ref={feedRef}
          objective={objective}
          onQuickPrompt={setInputPrompt}
          live={live}
          trace={trace}
          observations={observations}
          artifacts={artifacts}
          tasks={tasks}
          completedTasks={completedTasks}
          modelName={modelName}
          isInspectorOpen={isInspectorOpen}
          onToggleInspector={onToggleInspector}
          onSelectArtifact={onSelectArtifact}
          isVerified={isVerified}
          verCount={(verification?.results || []).length}
          digest={shortHash(trace?.checkpoint?.digest || "e931dcc03ceac399", 14)}
        />
      )}

      <McpMallPane objectiveGoal={objective?.goal} objectiveId={objective?.id} auto={true} />
      <Composer
        inputPrompt={inputPrompt}
        onInputChange={setInputPrompt}
        onSubmit={() => void handleSubmit()}
        isSubmitting={submitting}
        modelName={modelName}
        profile={auth?.profile || "STANDARD"}
        isInspectorOpen={isInspectorOpen}
        onToggleInspector={onToggleInspector}
      />
    </div>
  );
}

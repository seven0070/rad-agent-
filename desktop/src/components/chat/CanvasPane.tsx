// CanvasPane.tsx — Canvas-mode execution surface wrapper (StudioCanvas + BottomDrawer).
import React from "react";
import type { Artifact, ObjectiveRow, TaskRow } from "../../api";
import type { ToolObservation } from "../ToolCallPill";
import { StudioCanvas } from "../StudioCanvas";
import { BottomDrawer } from "./BottomDrawer";

interface CanvasPaneProps {
  objective: ObjectiveRow;
  tasks: TaskRow[];
  currentTaskId?: string;
  selectedNodeId?: string | null;
  onSelectNode: (nodeId: string, nodeType: "objective" | "task" | "verification") => void;
  isExecuting: boolean;
  observations: ToolObservation[];
  artifacts: Artifact[];
  currentTaskTitle?: string;
}

export const CanvasPane: React.FC<CanvasPaneProps> = ({
  objective,
  tasks,
  currentTaskId,
  selectedNodeId,
  onSelectNode,
  isExecuting,
  observations,
  artifacts,
  currentTaskTitle,
}) => {
  return (
    <div className="canvas-pane-root">
      <StudioCanvas
        objective={objective}
        tasks={tasks}
        currentTaskId={currentTaskId}
        selectedNodeId={selectedNodeId}
        onSelectNode={onSelectNode}
        isExecuting={isExecuting}
      />
      <BottomDrawer
        observations={observations}
        artifacts={artifacts}
        currentTaskTitle={currentTaskTitle}
      />
    </div>
  );
};
